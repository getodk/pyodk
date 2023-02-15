import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from mock import call

from pyodk._endpoints.forms import Form
from pyodk._utils.session import Session
from pyodk.client import Client
from pyodk.errors import PyODKError
from tests.resources import CONFIG_DATA, forms_data


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

    def test_update__requires_definition_or_attachments(self):
        with Client() as client:
            try:
                client.forms.update("foo")
            except PyODKError:
                pass
            else:
                self.fail("Exception expected")

    @patch("pyodk._endpoints.forms.FormDraftAttachmentService")
    @patch("pyodk._endpoints.forms.FormDraftService")
    def test_update__definition_only__creates_then_publishes_draft(
        self, draft_service_class, attachment_service_class
    ):
        mock_draft_service = MagicMock()
        mock_draft_service.create.return_value = True
        mock_draft_service.publish.return_value = True

        draft_service_class.return_value = mock_draft_service
        attachment_service_class.return_value = MagicMock()

        with Client() as client:
            client.forms.update("foo", definition="/some/path/file.xlsx")

        mock_draft_service.assert_has_calls(
            [
                call.create(
                    file_path="/some/path/file.xlsx",
                    form_id="foo",
                    project_id=None,
                    ignore_warnings=True,
                ),
                call.publish(form_id="foo", version=None, project_id=None),
            ]
        )

        mock_draft_service.assert_not_called()

    @patch("pyodk._endpoints.forms.datetime")
    @patch("pyodk._endpoints.forms.FormDraftAttachmentService")
    @patch("pyodk._endpoints.forms.FormDraftService")
    def test_update__attachments_only__creates_draft_attaches_attachments_then_publishes(
        self, draft_service_class, attachment_service_class, datetime_mock
    ):
        mock_draft_service = MagicMock()
        mock_draft_service.create.return_value = True
        mock_draft_service.publish.return_value = True

        mock_attachment_service = MagicMock()
        mock_attachment_service.upload.return_value = True

        draft_service_class.return_value = mock_draft_service
        attachment_service_class.return_value = mock_attachment_service

        datetime_mock.now.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0, 0)

        with Client() as client:
            client.forms.update(
                "foo", attachments=["/some/path/a.jpg", "/some/path/b.jpg"]
            )

        mock_draft_service.assert_has_calls(
            [
                call.create(
                    file_path=None, form_id="foo", project_id=None, ignore_warnings=True
                ),
                call.publish(
                    form_id="foo", version="2023-01-01T12:00:00", project_id=None
                ),
            ]
        )
        mock_attachment_service.assert_has_calls(
            [
                call.upload(file_path="/some/path/a.jpg", form_id="foo", project_id=None),
                call.upload(file_path="/some/path/b.jpg", form_id="foo", project_id=None),
            ]
        )

    @patch("pyodk._endpoints.forms.FormDraftAttachmentService")
    @patch("pyodk._endpoints.forms.FormDraftService")
    def test_update__attachments_and_definition__creates_draft_attaches_attachments_then_publishes(
        self, draft_service_class, attachment_service_class
    ):
        mock_draft_service = MagicMock()
        mock_draft_service.create.return_value = True
        mock_draft_service.publish.return_value = True

        mock_attachment_service = MagicMock()
        mock_attachment_service.upload.return_value = True

        draft_service_class.return_value = mock_draft_service
        attachment_service_class.return_value = mock_attachment_service

        with Client() as client:
            client.forms.update(
                "foo",
                definition="/some/path/form.xlsx",
                attachments=["/some/path/a.jpg", "/some/path/b.jpg"],
            )

        mock_draft_service.assert_has_calls(
            [
                call.create(
                    file_path="/some/path/form.xlsx",
                    form_id="foo",
                    project_id=None,
                    ignore_warnings=True,
                ),
                call.publish(form_id="foo", version=None, project_id=None),
            ]
        )
        mock_attachment_service.assert_has_calls(
            [
                call.upload(file_path="/some/path/a.jpg", form_id="foo", project_id=None),
                call.upload(file_path="/some/path/b.jpg", form_id="foo", project_id=None),
            ]
        )
