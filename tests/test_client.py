import os
from datetime import datetime
from pathlib import Path
from unittest import TestCase, skipUnless
from unittest.mock import MagicMock, patch

from pyodk.client import Client, Session, cfg

from tests.resources import (
    CACHE_FILE,
    CONFIG_FILE,
    RESOURCES,
    forms_data,
    submissions_data,
)
from tests.utils import utils
from tests.utils.entity_lists import create_new_or_get_entity_list
from tests.utils.forms import (
    create_new_form__md,
    create_new_form__xml,
    get_latest_form_version,
)
from tests.utils.md_table import md_table_to_bytes, md_table_to_temp_dir
from tests.utils.submissions import (
    create_new_or_get_last_submission,
    create_or_update_submission_with_comment,
)

E2E_WITH_REAL_REQUESTS = False


def create_test_forms(client: Client | None = None) -> Client:
    """
    Create test forms if they don't already exist.

    :param client: Client instance to use for API calls.
    :return: The original client instance, or a new one if none was provided.
    """
    if client is None:
        client = Client()
    create_new_form__xml(
        client=client,
        form_id="range_draft",
        form_def=forms_data.get_xml__range_draft(),
    )
    create_new_form__md(
        client=client,
        form_id="pull_data",
        form_def=forms_data.get_md__pull_data(),
    )
    create_new_form__md(
        client=client,
        form_id="non_ascii_form_id",
        form_def=forms_data.md__symbols,
    )
    create_new_form__md(
        client=client,
        form_id="✅",
        form_def=forms_data.md__dingbat,
    )
    create_new_form__md(
        client=client,
        form_id="upload_file",
        form_def=forms_data.md__upload_file,
    )
    return client


def create_test_submissions(client: Client | None = None) -> Client:
    """
    Create test submissions, if they don't already exist.

    :param client: Client instance to use for API calls.
    :return: The original client instance, or a new one if none was provided.
    """
    if client is None:
        client = Client()
    create_or_update_submission_with_comment(
        client=client,
        form_id="pull_data",
        instance_id="uuid:07ee9b2f-2271-474c-b9f3-c92ffba80c79",
    )
    create_or_update_submission_with_comment(
        client=client,
        form_id="pull_data",
        instance_id="uuid:4e2d1f60-aa3a-4065-bb97-af69b0cc8187",
    )
    return client


def create_test_entity_lists(client: Client | None = None) -> Client:
    """
    Create test entity lists, if they don't already exist.
    :param client: Client instance to use for API calls.
    :return: The original client instance, or a new one if none was provided.
    """
    if client is None:
        client = Client()
    create_new_or_get_entity_list(
        client=client,
        entity_list_name="pyodk_test_eln",
        entity_props=["test_label", "another_prop"],
    )
    return client


@skipUnless(condition=E2E_WITH_REAL_REQUESTS, reason="Requires Central instance.")
class TestUsage(TestCase):
    """Tests for experimenting with usage scenarios / general debugging / integration."""

    client: Client | None = None

    @classmethod
    def setUpClass(cls):
        cls.client = Client()
        create_test_forms(client=cls.client)
        create_test_submissions(client=cls.client)
        create_test_entity_lists(client=cls.client)

    def test_direct(self):
        projects = self.client.projects.list()
        forms = self.client.forms.list()
        submissions = self.client.submissions.list(form_id="pull_data")
        form_data = self.client.submissions.get_table(form_id="pull_data")
        form_data_params = self.client.submissions.get_table(
            form_id="pull_data",
            table_name="Submissions",
            count=True,
            select="__id,meta/instanceID,__system/formVersion,fruit",
        )
        comments = self.client.submissions.list_comments(
            form_id="pull_data",
            instance_id=next(s.instanceId for s in submissions),
        )
        self.assertIsNotNone(projects)
        self.assertIsNotNone(forms)
        self.assertIsNotNone(submissions)
        self.assertIsNotNone(form_data)
        self.assertIsNotNone(form_data_params)
        self.assertIsNotNone(comments)

    def test_direct_context(self):
        with Client() as client:
            projects = client.projects.list()
            forms = client.forms.list()
        self.assertIsNotNone(projects)
        self.assertIsNotNone(forms)

    def test_form_get_xml__returns_xform(self):
        """Should return the XForm XML document."""
        xml = self.client.forms.get_xml(form_id="pull_data")
        self.assertIsInstance(xml, str)
        self.assertIn("<h:title>pull_data</h:title>", xml)

    def test_form_create__new_definition_xml(self):
        """Should create a new form with the new definition."""
        form_id = self.client.session.get_xform_uuid()
        self.client.forms.create(
            form_id=form_id,
            definition=forms_data.get_xml__range_draft(form_id=form_id),
        )

    def test_form_create__new_definition_xlsx(self):
        """Should create a new form with the new definition."""
        form_def = forms_data.get_md__pull_data()
        wb = md_table_to_bytes(mdstr=form_def)
        form = self.client.forms.create(definition=wb)
        self.assertTrue(form.xmlFormId.startswith("uuid:"))

    def test_form_create__new_definition_xlsx_and_attachments(self):
        """Should create a new form with the new definition and attachment."""
        form_def = forms_data.get_md__pull_data()
        wb = md_table_to_bytes(mdstr=form_def)
        form = self.client.forms.create(
            definition=wb,
            attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
        )
        self.assertTrue(form.xmlFormId.startswith("uuid:"))

    # Below tests assume project has forms by these names already published.
    def test_form_update__new_definition(self):
        """Should create a new version with the new definition."""
        with utils.get_temp_file(suffix=".xml") as fp:
            fp.write_text(forms_data.get_xml__range_draft())
            self.client.forms.update(
                form_id="range_draft",
                definition=fp.as_posix(),
            )

    def test_form_update__new_definition_and_attachments(self):
        """Should create a new version with new definition and attachment."""
        # To test the API without a version_updater, a timestamped version is created.
        with md_table_to_temp_dir(
            form_id="pull_data", mdstr=forms_data.get_md__pull_data()
        ) as fp:
            self.client.forms.update(
                form_id="pull_data",
                definition=fp.as_posix(),
                attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
            )

    def test_form_update__new_definition_and_attachments__non_ascii_dingbat(self):
        """Should create a new version with new definition and attachment."""
        with md_table_to_temp_dir(
            form_id="✅", mdstr=forms_data.get_md__pull_data()
        ) as fp:
            self.client.forms.update(
                form_id="✅",
                definition=fp.as_posix(),
                attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
            )
            form = self.client.forms.get("✅")
            self.assertEqual(form.xmlFormId, "✅")

    def test_form_update__with_version_updater__non_ascii_specials(self):
        """Should create a new version with new definition."""
        self.client.forms.update(
            form_id="'=+/*-451%/%",
            attachments=[],
            version_updater=lambda v: datetime.now().isoformat(),
        )

    def test_form_update__attachments(self):
        """Should create a new version with new attachment."""
        self.client.forms.update(
            form_id="pull_data",
            attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
        )

    def test_form_update__attachments__with_version_updater(self):
        """Should create a new version with new attachment and updated version."""
        self.client.forms.update(
            form_id="pull_data",
            attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
            version_updater=lambda v: v + "_1",
        )

    def test_project_create_app_users__names_only(self):
        """Should create project app users."""
        self.client.projects.create_app_users(display_names=["test_role3", "test_user3"])

    def test_project_create_app_users__names_and_forms(self):
        """Should create project app users, and assign forms to them."""
        self.client.projects.create_app_users(
            display_names=["test_assign3", "test_assign_23"],
            forms=["range_draft", "pull_data"],
        )

    def test_submission_create__non_ascii(self):
        """Should create an instance of the form, encoded to utf-8."""
        form_id = "'=+/*-451%/%"
        iid = f"""scna+~!@#$%^&*()_+=-✅✅+{datetime.now().isoformat()}"""

        self.client.submissions.create(
            xml=submissions_data.get_xml__fruits(
                form_id=form_id,
                version=get_latest_form_version(client=self.client, form_id=form_id),
                instance_id=iid,
            ),
            form_id=form_id,
        )
        submission = self.client.submissions.get(form_id=form_id, instance_id=iid)
        self.assertEqual(iid, submission.instanceId)
        self.assertIsNone(submission.attachments)

    def test_submission_create__attachment(self):
        """Should create an instance of the form, encoded to utf-8."""
        form_id = "upload_file"
        file = Path(__file__).parent / "resources" / "forms" / "fruits.csv"
        submission = self.client.submissions.create(
            xml=submissions_data.upload_file_xml.format(
                iid=self.client.session.get_xform_uuid(),
                file_name=file.name,
            ),
            form_id=form_id,
            attachments=[file],
        )
        attachment = submission.attachments[0]
        self.assertEqual(file.name, attachment.name)
        self.assertEqual(True, attachment.exists)

    def test_submission_edit__non_ascii(self):
        """Should edit an existing instance of the form, encoded to utf-8."""
        # The "instance_id" remains the id of the first submission, not the
        # instanceID/deprecatedID used in the XML.
        form_id = "'=+/*-451%/%"
        iid = """sena_~~!@#$%^&*()_+=-✅✅"""

        # So we have a submission to edit, create one or find the most recent prior edit.
        old_iid = create_new_or_get_last_submission(
            client=self.client,
            form_id=form_id,
            instance_id=iid,
        )
        now = datetime.now().isoformat()
        self.client.submissions.edit(
            xml=submissions_data.get_xml__fruits(
                form_id=form_id,
                version=get_latest_form_version(client=self.client, form_id=form_id),
                instance_id=iid + now,
                deprecated_instance_id=old_iid,
            ),
            form_id=form_id,
            instance_id=iid,
            comment=f"pyODK edit {now}",
        )

    def test_entities__create_and_query(self):
        """Should create a new entity, and query it afterwards via list() or get_table()."""
        self.client.entities.default_entity_list_name = "pyodk_test_eln"
        entity = self.client.entities.create(
            label="test_label",
            data={"test_label": "test_value", "another_prop": "another_value"},
        )
        entity_list = self.client.entities.list()
        # entities.create() has entities.currentVersion.data, entities.list() doesn't.
        self.assertIn(entity.uuid, [e.uuid for e in entity_list])
        entity_data = self.client.entities.get_table(select="__id")
        self.assertIn(entity.uuid, [d["__id"] for d in entity_data["value"]])

    def test_entities__update(self):
        """Should update the entity, via either base_version or force."""
        self.client.entities.default_entity_list_name = "pyodk_test_eln"
        entity = self.client.entities.create(
            label="test_label",
            data={"test_label": "test_value", "another_prop": "another_value"},
        )
        updated = self.client.entities.update(
            label="test_label",
            data={"test_label": "test_value2", "another_prop": "another_value2"},
            uuid=entity.uuid,
            base_version=entity.currentVersion.version,
        )
        self.assertEqual("test_value2", updated.currentVersion.data["test_label"])
        forced = self.client.entities.update(
            label="test_label",
            data={"test_label": "test_value3", "another_prop": "another_value3"},
            uuid=entity.uuid,
            force=True,
        )
        self.assertEqual("test_value3", forced.currentVersion.data["test_label"])

    def test_entity__merge__new(self):
        """Should create a new Entity List, and merge in some new data."""
        self.client.entity_lists.default_entity_list_name = (
            self.client.session.get_xform_uuid()
        )
        entity_list = self.client.entity_lists.create()
        self.client.entities.merge(
            data=[
                {"label": "Sydney", "state": "NSW"},
                {"label": "Melbourne", "state": "VIC"},
            ],
            entity_list_name=entity_list.name,
        )
        entity_data = self.client.entities.get_table(entity_list_name=entity_list.name)
        self.assertEqual(2, len(entity_data["value"]))

    def test_entity__merge__existing__add_props__delete_unmatched(self):
        """Should create a new Entity List, and merge in some new data."""
        self.client.entity_lists.default_entity_list_name = (
            self.client.session.get_xform_uuid()
        )
        entity_list = self.client.entity_lists.create()
        self.client.entity_lists.add_property(
            name="state", entity_list_name=entity_list.name
        )
        self.client.entities.create_many(
            data=[
                {"label": "Sydney", "state": "VIC"},
                {"label": "Darwin", "state": "NT"},
            ],
            entity_list_name=entity_list.name,
        )
        # Add postcode property, Add Brisbane, update Sydney, delete Darwin.
        self.client.entities.merge(
            data=[
                {"label": "Sydney", "state": "NSW", "postcode": "2001"},
                {"label": "Brisbane", "state": "QLD", "postcode": "4000"},
            ],
            entity_list_name=entity_list.name,
            add_new_properties=True,
            delete_not_matched=True,
        )
        entity_data = self.client.entities.get_table(entity_list_name=entity_list.name)
        expected = [
            {"label": "Sydney", "state": "NSW", "postcode": "2001"},
            {"label": "Brisbane", "state": "QLD", "postcode": "4000"},
        ]
        observed = [
            {k: o.get(k) for k in ("state", "label", "postcode")}
            for o in entity_data["value"]
        ]
        self.assertTrue(
            len(expected) == len(observed)
            and all(e in observed for e in expected)
            and expected[0].keys() == observed[0].keys(),
            observed,
        )

    def test_entity__merge__existing__ignore_props__keep_unmatched(self):
        """Should create a new Entity List, and merge in some new data."""
        self.client.entity_lists.default_entity_list_name = (
            self.client.session.get_xform_uuid()
        )
        entity_list = self.client.entity_lists.create()
        self.client.entity_lists.add_property(
            name="state", entity_list_name=entity_list.name
        )
        self.client.entities.create_many(
            data=[
                {"label": "Sydney", "state": "VIC"},
                {"label": "Darwin", "state": "NT"},
            ],
            entity_list_name=entity_list.name,
        )
        # Skip postcode property, add Brisbane, update Sydney, keep Darwin.
        self.client.entities.merge(
            data=[
                {"label": "Sydney", "state": "NSW", "postcode": "2000"},  # update
                {"label": "Brisbane", "state": "QLD", "postcode": "4000"},  # insert
            ],
            entity_list_name=entity_list.name,
            add_new_properties=False,
            delete_not_matched=False,
        )
        entity_data = self.client.entities.get_table(entity_list_name=entity_list.name)
        expected = [
            {"label": "Sydney", "state": "NSW"},
            {"label": "Brisbane", "state": "QLD"},
            {"label": "Darwin", "state": "NT"},
        ]
        observed = [
            {k: o.get(k) for k in ("state", "label")} for o in entity_data["value"]
        ]
        self.assertTrue(
            len(expected) == len(observed)
            and all(e in observed for e in expected)
            and expected[0].keys() == observed[0].keys(),
            observed,
        )

    def test_entity_lists__list(self):
        """Should return a list of Entity Lists."""
        observed = self.client.entity_lists.list()
        self.assertGreater(len(observed), 0)

    def test_entity_lists__create_and_query(self):
        """Should create a new Entity List, and query it afterwards via list()."""
        self.client.entity_lists.default_entity_list_name = (
            self.client.session.get_xform_uuid()
        )
        entity_list = self.client.entity_lists.create()
        entity_lists = self.client.entity_lists.list()
        self.assertIn(
            (entity_list.name, entity_list.projectId),
            [(e.name, e.projectId) for e in entity_lists],
        )

    def test_entity_lists__add_property(self):
        """Should create a new property on the Entity List."""
        self.client.entity_lists.default_entity_list_name = (
            self.client.session.get_xform_uuid()
        )
        self.client.entity_lists.create()
        self.client.entity_lists.add_property(name="test")
        entity_list = self.client.entity_lists.get()
        self.assertEqual(["test"], [p.name for p in entity_list.properties])


def client_init__default():
    """Read the config file is in the default location."""
    return Client()


def client_init__with_kwargs():
    """Use the defaults but specify them manually."""
    return Client(
        config=cfg.read_config(),
        cache_path=cfg.get_cache_path(),
    )


def client_init__with_config__with_session__with_cache():
    """Provide a pre-made Config and customised Session."""
    config = cfg.read_config()
    return Client(
        config=config,
        session=Session(
            base_url=config.central.base_url,
            api_version="v1",
            username=config.central.username,
            password=config.central.password,
            cache_path=cfg.get_cache_path(),
        ),
    )


def client_init__with_config__with_session__no_cache(config: cfg.Config | None = None):
    """Provide a pre-made Config and customised Session, but don't write a session cache."""
    if not config:
        config = cfg.read_config()
    return Client(
        config=config,
        session=Session(
            base_url=config.central.base_url,
            api_version="v1",
            username=config.central.username,
            password=config.central.password,
        ),
    )


class TestClientInit(TestCase):
    patterns = (
        client_init__default,
        client_init__with_kwargs,
        client_init__with_config__with_session__with_cache,
        client_init__with_config__with_session__no_cache,
    )

    @patch("pyodk._utils.session.AuthService.get_new_token", MagicMock(return_value="x"))
    @patch("pyodk._utils.session.AuthService.verify_token", MagicMock(return_value="x"))
    def test_init_patterns_with_open(self):
        """Should find that Client can be opened using supported init patterns."""
        cf = {
            "PYODK_CONFIG_FILE": CONFIG_FILE.as_posix(),
            "PYODK_CACHE_FILE": CACHE_FILE.as_posix(),
        }
        for i, init in enumerate(self.patterns):
            with self.subTest(i), patch.dict(os.environ, cf, clear=True):
                client = init()
                client.open()
                self.assertEqual("Bearer x", client.session.headers["Authorization"])

    @skipUnless(condition=E2E_WITH_REAL_REQUESTS, reason="Requires Central instance.")
    def test_init_patterns_with_request(self):
        """Should find that Client can be used with supported init patterns."""
        for i, init in enumerate(self.patterns):
            with self.subTest(i):
                client = init()
                client.forms.list()

    @skipUnless(condition=E2E_WITH_REAL_REQUESTS, reason="Requires Central instance.")
    def test_init_with_session_but_no_cache_does_not_read_or_write_files(self):
        """Should find that for this pattern config files are not manipulated."""
        config = cfg.read_config()
        with (
            patch("pyodk._utils.config.read_toml") as read_toml,
            patch("pyodk.client.cfg.read_config") as read_config,
            patch("pyodk._endpoints.auth.config.read_cache_token") as read_cache_token,
            patch("pyodk._endpoints.auth.config.write_cache") as write_cache,
            patch("pyodk._utils.config.delete_cache") as delete_cache,
        ):
            client = client_init__with_config__with_session__no_cache(config=config)
            client.forms.list()
            token = client.session.headers.get("Authorization", None)
            self.assertTrue(token and token.startswith("Bearer"))
            client2 = client_init__with_config__with_session__no_cache(config=config)
            client2.forms.list()
            token2 = client.session.headers.get("Authorization", None)
            self.assertTrue(token2 and token2.startswith("Bearer"))
            # May be useful to assert token/token2 are different here, but it seems Central
            # caches sessions, so the same token comes back - presumably unless there is
            # an explicit logout request, which pyodk doesn't current do on close/exit.
            self.assertEqual(0, read_toml.call_count)
            self.assertEqual(0, read_config.call_count)
            self.assertEqual(0, read_cache_token.call_count)
            self.assertEqual(0, write_cache.call_count)
            self.assertEqual(0, delete_cache.call_count)
