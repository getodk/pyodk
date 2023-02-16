from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Callable
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.form_draft_attachments import FormDraftAttachmentService
from pyodk._endpoints.form_drafts import FormDraftService
from pyodk._endpoints.forms import Form
from pyodk._utils.session import Session
from pyodk.client import Client
from pyodk.errors import PyODKError
from tests.resources import CONFIG_DATA, forms_data


@dataclass
class MockContext:
    fd_create: MagicMock
    fd_publish: MagicMock
    fda_upload: MagicMock
    dt: MagicMock


def get_mock_context(func) -> Callable:
    """
    Inject a context object with mocks for testing forms: drafts, attachments, etc.

    To use, add a keyword argument "ctx" to the decorated function.
    """

    @wraps(func)
    def patched(*args, **kwargs):
        with patch.object(
            FormDraftService, "create", return_value=True
        ) as create, patch.object(
            FormDraftService, "publish", return_value=True
        ) as publish, patch.object(
            FormDraftAttachmentService, "upload", return_value=True
        ) as upload, patch(
            "pyodk._endpoints.forms.datetime"
        ) as dt:
            dt.now.return_value = datetime(2023, 1, 1, 12, 0, 0, 0)
            ctx = MockContext(
                fd_create=create, fd_publish=publish, fda_upload=upload, dt=dt
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

    def test_update__def_or_attach_required(self):
        """Should raise an error if both 'definition' and 'attachments' are None."""
        with self.assertRaises(PyODKError) as err:
            client = Client()
            client.forms.update("foo")

        self.assertEqual(
            "Must specify a form definition and/or attachments.", err.exception.args[0]
        )

    @get_mock_context
    def test_update__def_only__create_publish_no_upload2(self, ctx: MockContext):
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
        ctx.fda_upload.call_count = 2
        ctx.fda_upload.assert_any_call(
            file_path="/some/path/a.jpg", form_id="foo", project_id=None
        )
        ctx.fda_upload.assert_any_call(
            file_path="/some/path/b.jpg", form_id="foo", project_id=None
        )
        ctx.fd_publish.assert_called_once_with(
            form_id="foo", version="2023-01-01T12:00:00", project_id=None
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
        ctx.fda_upload.call_count = 2
        ctx.fda_upload.assert_any_call(
            file_path="/some/path/a.jpg", form_id="foo", project_id=None
        )
        ctx.fda_upload.assert_any_call(
            file_path="/some/path/b.jpg", form_id="foo", project_id=None
        )
        ctx.fd_publish.assert_called_once_with(
            form_id="foo", version=None, project_id=None
        )
