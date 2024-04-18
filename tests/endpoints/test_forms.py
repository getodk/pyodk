from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from pyodk._endpoints.form_draft_attachments import FormDraftAttachmentService
from pyodk._endpoints.form_drafts import FormDraftService
from pyodk._endpoints.form_drafts import log as form_drafts_log
from pyodk._endpoints.forms import Form, FormService
from pyodk._utils.session import Session
from pyodk.client import Client
from pyodk.errors import PyODKError

from tests.resources import CONFIG_DATA, forms_data
from tests.utils import utils


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
        with (
            patch.object(
                FormService,
                "get",
                return_value=Form(**forms_data.test_forms["response_data"][0]),
            ) as form_get,
            patch.object(FormDraftService, "create", return_value=True) as create,
            patch.object(FormDraftService, "publish", return_value=True) as publish,
            patch.object(
                FormDraftAttachmentService, "upload", return_value=True
            ) as upload,
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

    def test_create__ok(self):
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
            file_path="/some/path/file.xlsx",
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
            file_path=None,
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
            file_path="/some/path/form.xlsx",
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

        def mock_wrap_error(**kwargs):
            return kwargs["value"]

        with (
            patch.object(Session, "response_or_error") as mock_response,
            patch("pyodk._utils.validators.wrap_error", mock_wrap_error),
            patch("builtins.open", mock_open(), create=True) as mock_open_patch,
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
            data=mock_open_patch.return_value,
        )

    def test_update__def_encoding(self):
        """Should find that the URL and fallback header are url-encoded."""
        test_cases = (
            ("foo", "/some/path/foo.xlsx", "projects/1/forms/foo/draft", "foo"),
            ("foo", "/some/path/✅.xlsx", "projects/1/forms/foo/draft", "foo"),
            (None, "/some/path/✅.xlsx", "projects/1/forms/%E2%9C%85/draft", "%E2%9C%85"),
            ("✅", "/some/path/✅.xlsx", "projects/1/forms/%E2%9C%85/draft", "%E2%9C%85"),
            (
                "✅",
                "/some/path/foo.xlsx",
                "projects/1/forms/%E2%9C%85/draft",
                "%E2%9C%85",
            ),
            (None, "/some/path/foo.xlsx", "projects/1/forms/foo/draft", "foo"),
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
