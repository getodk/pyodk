from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.form_draft_attachments import (
    FormAttachment,
    FormDraftAttachmentService,
)
from pyodk._endpoints.form_drafts import (
    CONTENT_TYPES,
    FormDraftService,
    get_definition_data,
)
from pyodk._endpoints.form_drafts import (
    log as form_drafts_log,
)
from pyodk._endpoints.forms import Form, FormService
from pyodk._utils.session import Session
from pyodk.client import Client
from pyodk.errors import PyODKError

from tests.resources import CONFIG_DATA, RESOURCES, forms_data
from tests.utils import utils
from tests.utils.md_table import md_table_to_bytes, md_table_to_bytes_xls


@dataclass
class MockContext:
    form_get: MagicMock
    fd_create: MagicMock
    fd_publish: MagicMock
    fda_upload: MagicMock
    dt: MagicMock
    now: datetime = datetime(2023, 1, 1, 12, 0, 0, 0)


def get_mock_context(func) -> Callable:
    """
    Inject a context object with mocks for testing forms: drafts, attachments, etc.

    To use, add a keyword argument "ctx" to the decorated function.
    """

    @wraps(func)
    def patched(*args, **kwargs):
        fa = FormAttachment(
            name="fruits.csv",
            type="file",
            hash="b61381f802d5ca6bc054e49e32471500",
            exists=True,
            blobExists=True,
            datasetExists=False,
            updatedAt=datetime.now(),
        )
        with (
            patch.object(
                FormService,
                "get",
                return_value=Form(**forms_data.test_forms["response_data"][0]),
            ) as form_get,
            patch.object(FormDraftService, "create", return_value=True) as create,
            patch.object(FormDraftService, "publish", return_value=True) as publish,
            patch.object(FormDraftAttachmentService, "upload", return_value=fa) as upload,
            patch("pyodk._endpoints.forms.datetime") as dt,
        ):
            dt.now.return_value = MockContext.now
            ctx = MockContext(
                form_get=form_get,
                fd_create=create,
                fd_publish=publish,
                fda_upload=upload,
                dt=dt,
            )
            kwargs.update({"ctx": ctx})
            return func(*args, **kwargs)

    return patched


@patch("pyodk._utils.session.Auth.login", MagicMock())
@patch("pyodk._utils.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestForms(TestCase):
    def test_list__ok(self):
        """Should return a list of FormType objects."""
        fixture = forms_data.test_forms
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"]
            with Client() as client:
                observed = client.forms.list()
        self.assertEqual(4, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, Form)

    def test_get__ok(self):
        """Should return a FormType object."""
        fixture = forms_data.test_forms
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            with Client() as client:
                # Specify project
                observed = client.forms.get(
                    project_id=fixture["project_id"],
                    form_id=fixture["response_data"][0]["xmlFormId"],
                )
                self.assertIsInstance(observed, Form)
                # Use default
                observed = client.forms.get(
                    form_id=fixture["response_data"][0]["xmlFormId"]
                )
                self.assertIsInstance(observed, Form)

    @get_mock_context
    def test_create__ok(self, ctx: MockContext):
        """Should return a FormType object."""
        fixture = forms_data.test_forms
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][1]
            with Client() as client, utils.get_temp_file(suffix=".xml") as fp:
                fp.write_text(forms_data.get_xml__range_draft())
                # Specify project
                observed = client.forms.create(
                    definition=fp,
                    project_id=fixture["project_id"],
                    form_id=fixture["response_data"][1]["xmlFormId"],
                )
                self.assertIsInstance(observed, Form)
                # Use default
                observed = client.forms.create(
                    definition=fp, form_id=fixture["response_data"][1]["xmlFormId"]
                )
                self.assertIsInstance(observed, Form)

    @get_mock_context
    def test_create__with_attachments__ok(self, ctx: MockContext):
        """Should return a FormType object."""
        fixture = forms_data.test_forms
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][1]
            with Client() as client, utils.get_temp_file(suffix=".xml") as fp:
                fp.write_text(forms_data.get_xml__range_draft())
                observed = client.forms.create(
                    definition=fp,
                    project_id=fixture["project_id"],
                    form_id=fixture["response_data"][1]["xmlFormId"],
                    attachments=["/some/path/a.jpg", "/some/path/b.jpg"],
                )
                self.assertIsInstance(observed, Form)
                self.assertEqual(2, ctx.fda_upload.call_count)
                ctx.fd_publish.assert_called_once_with(
                    form_id=fixture["response_data"][1]["xmlFormId"],
                    project_id=fixture["project_id"],
                )

    def test_form_attachment_upload__sets_content_type(self):
        """Should return a FormAttachment object and set the Content-Type header."""
        fixture = forms_data.test_forms
        fixture_attachments = forms_data.test_form_attachments

        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture_attachments[0]
            with Client() as client, utils.get_temp_file(suffix=".jpg") as fa_jpg:
                fda = FormDraftAttachmentService(session=client.session)
                observed = fda.upload(
                    file_path=(RESOURCES / "forms" / "fruits.csv").as_posix(),
                    project_id=fixture["project_id"],
                    form_id=fixture["response_data"][1]["xmlFormId"],
                )
                self.assertIsInstance(observed, bool)
                self.assertEqual(
                    {"Content-Type": "text/csv", "Transfer-Encoding": "chunked"},
                    mock_session.call_args.kwargs["headers"],
                )
                observed = fda.upload(
                    file_path=fa_jpg.as_posix(),
                    project_id=fixture["project_id"],
                    form_id=fixture["response_data"][1]["xmlFormId"],
                )
                self.assertIsInstance(observed, bool)
                self.assertEqual(
                    {"Content-Type": "image/jpeg", "Transfer-Encoding": "chunked"},
                    mock_session.call_args.kwargs["headers"],
                )

    def test_update__def_or_attach_required(self):
        """Should raise an error if both 'definition' and 'attachments' are None."""
        with self.assertRaises(PyODKError) as err:
            client = Client()
            client.forms.update("foo")

        self.assertEqual(
            "Must specify a form definition and/or attachments.", err.exception.args[0]
        )

    @get_mock_context
    def test_update__def_only__create_publish_no_upload(self, ctx: MockContext):
        """Should call fd.create and fd.publish, not fda.upload (nothing to upload)."""
        client = Client()
        client.forms.update("foo", definition="/some/path/file.xlsx")
        ctx.fd_create.assert_called_once_with(
            definition="/some/path/file.xlsx",
            form_id="foo",
            project_id=None,
        )
        ctx.fda_upload.assert_not_called()
        ctx.fd_publish.assert_called_once_with(
            form_id="foo", version=None, project_id=None
        )

    @get_mock_context
    def test_update__attach_only__create_upload_publish(self, ctx: MockContext):
        """Should call fd.create, fda.upload, and fd.publish."""
        client = Client()
        client.forms.update("foo", attachments=["/some/path/a.jpg", "/some/path/b.jpg"])
        ctx.fd_create.assert_called_once_with(
            definition=None,
            form_id="foo",
            project_id=None,
        )
        self.assertEqual(2, ctx.fda_upload.call_count)
        ctx.fda_upload.assert_any_call(
            file_path="/some/path/a.jpg", form_id="foo", project_id=None
        )
        ctx.fda_upload.assert_any_call(
            file_path="/some/path/b.jpg", form_id="foo", project_id=None
        )
        ctx.fd_publish.assert_called_once_with(
            form_id="foo", version=ctx.now.isoformat(), project_id=None
        )

    @get_mock_context
    def test_update__attach_only__version_updater(self, ctx: MockContext):
        """Should call the version_updater."""
        client = Client()
        client.forms.update(
            "foo",
            attachments=["/some/path/a.jpg", "/some/path/b.jpg"],
            version_updater=lambda x: "v2xyz",
        )
        ctx.fd_publish.assert_called_once_with(
            form_id="foo", version="v2xyz", project_id=None
        )

    @get_mock_context
    def test_update__def_and_attach__create_upload_publish(self, ctx: MockContext):
        """Should call fd.create, fda.upload, and fd.publish."""
        client = Client()
        client.forms.update(
            "foo",
            definition="/some/path/form.xlsx",
            attachments=["/some/path/a.jpg", "/some/path/b.jpg"],
        )
        ctx.fd_create.assert_called_once_with(
            definition="/some/path/form.xlsx",
            form_id="foo",
            project_id=None,
        )
        self.assertEqual(2, ctx.fda_upload.call_count)
        ctx.fda_upload.assert_any_call(
            file_path="/some/path/a.jpg", form_id="foo", project_id=None
        )
        ctx.fda_upload.assert_any_call(
            file_path="/some/path/b.jpg", form_id="foo", project_id=None
        )
        ctx.fd_publish.assert_called_once_with(
            form_id="foo", version=None, project_id=None
        )

    @staticmethod
    def update__def_encoding_steps(
        form_id: str, definition: str, expected_url: str, expected_fallback_id: str
    ):
        client = Client()

        def mock_get_def_data(*args, **kwargs):
            return "", CONTENT_TYPES[".xlsx"], ""

        with (
            patch.object(Session, "response_or_error") as mock_response,
            patch("pyodk._endpoints.form_drafts.get_definition_data", mock_get_def_data),
        ):
            client.forms.update(form_id, definition=definition)
        mock_response.assert_any_call(
            method="POST",
            url=expected_url,
            logger=form_drafts_log,
            headers={
                "Content-Type": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                "X-XlsForm-FormId-Fallback": expected_fallback_id,
            },
            params={"ignoreWarnings": True},
            data="",
        )

    def test_update__def_encoding(self):
        """Should find that the URL and fallback header are url-encoded."""
        test_cases = (
            ("foo", "/some/path/foo.xlsx", "projects/1/forms/foo/draft", "foo"),
            ("foo", "/some/path/✅.xlsx", "projects/1/forms/foo/draft", "foo"),
            ("✅", "/some/path/✅.xlsx", "projects/1/forms/%E2%9C%85/draft", "%E2%9C%85"),
            (
                "✅",
                "/some/path/foo.xlsx",
                "projects/1/forms/%E2%9C%85/draft",
                "%E2%9C%85",
            ),
        )
        for case in test_cases:
            with self.subTest(msg=str(case)):
                self.update__def_encoding_steps(*case)

    def test_update__no_def_no_attach__raises(self):
        """Should raise an error if there is no definition or attachment."""
        client = Client()
        with self.assertRaises(PyODKError) as err:
            client.forms.update("foo")
        self.assertEqual(
            "Must specify a form definition and/or attachments.", err.exception.args[0]
        )

    def test_update__with_def_with_version_updater__raises(self):
        """Should raise an error if there is a definition and version_updater."""
        client = Client()
        with self.assertRaises(PyODKError) as err:
            client.forms.update(
                form_id="foo",
                definition="/some/path/form.xlsx",
                version_updater=lambda x: "v2",
            )
        self.assertEqual(
            "Must not specify both a definition and version_updater.",
            err.exception.args[0],
        )


class TestGetDefinitionData(TestCase):
    def test_get_definition_data__xml_file(self):
        """Should get the expected definition data and content type."""
        form_data = forms_data.get_xml__range_draft()
        with utils.get_temp_file(suffix=".xml") as fp:
            fp.write_text(form_data, newline="\n")
            expected_stem = fp.stem
            definition_data, content_type, file_path_stem = get_definition_data(
                definition=fp
            )
        self.assertEqual(form_data, definition_data.decode("utf-8"))
        self.assertEqual(CONTENT_TYPES[".xml"], content_type)
        self.assertEqual(expected_stem, file_path_stem)

    def test_get_definition_data__xml_str(self):
        """Should get the expected definition data and content type."""
        form_data = forms_data.get_xml__range_draft()
        definition_data, content_type, file_path_stem = get_definition_data(
            definition=form_data
        )
        self.assertEqual(form_data, definition_data.decode("utf-8"))
        self.assertEqual(CONTENT_TYPES[".xml"], content_type)
        self.assertEqual(None, file_path_stem)

    def test_get_definition_data__xls_file(self):
        """Should get the expected definition data and content type."""
        form_data = md_table_to_bytes_xls(forms_data.get_md__pull_data())
        with utils.get_temp_file(suffix=".xls") as fp:
            fp.write_bytes(form_data)
            expected_stem = fp.stem
            definition_data, content_type, file_path_stem = get_definition_data(
                definition=fp
            )
        self.assertEqual(form_data, definition_data)
        self.assertEqual(CONTENT_TYPES[".xls"], content_type)
        self.assertEqual(expected_stem, file_path_stem)

    def test_get_definition_data__xls_bytes(self):
        """Should get the expected definition data and content type."""
        form_data = md_table_to_bytes_xls(forms_data.get_md__pull_data())
        definition_data, content_type, file_path_stem = get_definition_data(
            definition=form_data
        )
        self.assertEqual(form_data, definition_data)
        self.assertEqual(CONTENT_TYPES[".xls"], content_type)
        self.assertEqual(None, file_path_stem)

    def test_get_definition_data__xlsx_file(self):
        """Should get the expected definition data and content type."""
        form_data = md_table_to_bytes(forms_data.get_md__pull_data())
        with utils.get_temp_file(suffix=".xlsx") as fp:
            fp.write_bytes(form_data)
            expected_stem = fp.stem
            definition_data, content_type, file_path_stem = get_definition_data(
                definition=fp
            )
        self.assertEqual(form_data, definition_data)
        self.assertEqual(CONTENT_TYPES[".xlsx"], content_type)
        self.assertEqual(expected_stem, file_path_stem)

    def test_get_definition_data__xlsx_bytes(self):
        """Should get the expected definition data and content type."""
        form_data = md_table_to_bytes(forms_data.get_md__pull_data())
        definition_data, content_type, file_path_stem = get_definition_data(
            definition=form_data
        )
        self.assertEqual(form_data, definition_data)
        self.assertEqual(CONTENT_TYPES[".xlsx"], content_type)
        self.assertEqual(None, file_path_stem)

    def test_get_definition_data__unknown_file(self):
        """Should throw an error if an unknown file extension is specified."""
        form_data = forms_data.get_xml__range_draft()
        with utils.get_temp_file(suffix=".docx") as fp:
            fp.write_text(form_data, newline="\n")
            with self.assertRaises(PyODKError) as err:
                get_definition_data(definition=fp)
            self.assertIn("unexpected file extension", err.exception.args[0])

    def test_get_definition_data__unknown_bytes(self):
        """Should throw an error if an unknown file type is provided."""
        with self.assertRaises(PyODKError) as err:
            get_definition_data(definition=b"hello world")
        self.assertIn("unexpected file type", err.exception.args[0])
