from datetime import datetime
from unittest import TestCase, skip

from pyodk.client import Client
from tests.resources import RESOURCES


@skip
class TestUsage(TestCase):
    """Tests for experimenting with usage scenarios / general debugging / integration."""

    def test_direct(self):
        client = Client()
        projects = client.projects.list()
        forms = client.forms.list()
        submissions = client.submissions.list(form_id=forms[3].xmlFormId)
        form_data = client.submissions.get_table(form_id=forms[3].xmlFormId)
        form_data_params = client.submissions.get_table(
            form_id="range",
            table_name="Submissions",
            count=True,
        )
        comments = client.submissions.list_comments(
            form_id="range",
            instance_id="uuid:2c296eae-2708-4a89-bfe7-0f2d440b7fe8",
        )
        print([projects, forms, submissions, form_data, form_data_params, comments])

    def test_direct_context(self):
        with Client() as client:
            projects = client.projects.list()
            forms = client.forms.list()
        print(projects, forms)

    # Below tests assume project has forms by these names already published.
    def test_form_update__new_definition(self):
        """Should create a new version with the new definition."""
        with Client() as client:
            client.forms.update(
                form_id="range_draft",
                definition=(RESOURCES / "forms" / "range_draft.xml").as_posix(),
            )

    def test_form_update__new_definition_and_attachments(self):
        """Should create a new version with new definition and attachment."""
        with Client() as client:
            client.forms.update(
                form_id="pull_data",
                definition=(RESOURCES / "forms" / "pull_data.xlsx").as_posix(),
                attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
            )

    def test_form_update__new_definition_and_attachments__non_ascii_dingbat(self):
        """Should create a new version with new definition and attachment."""
        with Client() as client:
            client.forms.update(
                form_id="✅",
                definition=(RESOURCES / "forms" / "✅.xlsx").as_posix(),
                attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
            )
            form = client.forms.get("✅")
            self.assertEqual(form.xmlFormId, "✅")

    def test_form_update__with_version_updater__non_ascii_specials(self):
        """Should create a new version with new definition and attachment."""
        with Client() as client:
            client.forms.update(
                form_id="'=+/*-451%/%",
                attachments=[],
                version_updater=lambda v: datetime.now().isoformat(),
            )

    def test_form_update__attachments(self):
        """Should create a new version with new attachment."""
        with Client() as client:
            client.forms.update(
                form_id="pull_data",
                attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
            )

    def test_form_update__attachments__with_version_updater(self):
        """Should create a new version with new attachment and updated version."""
        with Client() as client:
            client.forms.update(
                form_id="pull_data",
                attachments=[(RESOURCES / "forms" / "fruits.csv").as_posix()],
                version_updater=lambda v: v + "_1",
            )

    def test_project_create_app_users__names_only(self):
        """Should create project app users."""
        client = Client()
        client.projects.create_app_users(display_names=["test_role3", "test_user3"])

    def test_project_create_app_users__names_and_forms(self):
        """Should create project app users, and assign forms to them."""
        client = Client()
        client.projects.create_app_users(
            display_names=["test_assign3", "test_assign_23"],
            forms=["range", "pull_data"],
        )

    def test_submission_create__non_ascii(self):
        """Should create an instance of the form, encoded to utf-8."""
        client = Client()
        xml = """
        <data id="'=+/*-451%/%" version="1">
          <meta>
            <instanceID>~!@#$%^&*()_+=-✅✅</instanceID>
          </meta>
          <fruit>Banana</fruit>
          <note_fruit/>
        </data>
        """
        client.submissions.create(xml=xml, form_id="'=+/*-451%/%")
        submission = client.submissions.get(
            form_id="'=+/*-451%/%", instance_id="~!@#$%^&*()_+=-✅✅"
        )
        self.assertEqual("~!@#$%^&*()_+=-✅✅", submission.instanceId)

    def test_submission_edit__non_ascii(self):
        """Should edit an existing instance of the form, encoded to utf-8."""
        client = Client()
        # The "instance_id" remains the id of the first submission, not the
        # instanceID/deprecatedID used in the XML.
        xml = """
        <data id="'=+/*-451%/%" version="1">
          <meta>
            <deprecatedID>~!@#$%^&*()_+=-✘✘</deprecatedID>
            <instanceID>~!@#$%^&*()_+=-✘✘✘</instanceID>
          </meta>
          <fruit>Papaya</fruit>
          <note_fruit/>
        </data>
        """
        client.submissions.edit(
            xml=xml, form_id="'=+/*-451%/%", instance_id="~!@#$%^&*()_+=-✅✅"
        )
