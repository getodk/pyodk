from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.submission_attachments import SubmissionAttachment
from pyodk._endpoints.submissions import Submission
from pyodk._utils.session import Session
from pyodk.client import Client
from pyodk.errors import PyODKError

from tests.resources import (
    CONFIG_DATA,
    RESOURCES,
    submission_attachments_data,
    submissions_data,
)


@patch("pyodk._utils.session.Auth.login", MagicMock())
@patch("pyodk._utils.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestSubmissions(TestCase):
    def test_list__ok(self):
        """Should return a list of Submission objects."""
        fixture = submissions_data.test_submissions
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"]
            with Client() as client:
                observed = client.submissions.list(form_id="range")
        self.assertEqual(4, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, Submission)

    def test_get__ok(self):
        """Should return a Submission object."""
        fixture = submissions_data.test_submissions
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            with Client() as client:
                # Specify project
                observed = client.submissions.get(
                    project_id=fixture["project_id"],
                    form_id=fixture["form_id"],
                    instance_id=fixture["response_data"][0]["instanceId"],
                )
                self.assertIsInstance(observed, Submission)
                # Use default
                observed = client.submissions.get(
                    form_id=fixture["form_id"],
                    instance_id=fixture["response_data"][0]["instanceId"],
                )
                self.assertIsInstance(observed, Submission)

    def test_create__ok(self):
        """Should return a Submission object."""
        fixture = submissions_data.test_submissions
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            with Client() as client:
                # Specify project
                observed = client.submissions.create(
                    project_id=fixture["project_id"],
                    form_id=fixture["form_id"],
                    xml=submissions_data.test_xml,
                )
                self.assertIsInstance(observed, Submission)
                # Use default
                observed = client.submissions.create(
                    form_id=fixture["form_id"],
                    xml=submissions_data.test_xml,
                )
                self.assertIsInstance(observed, Submission)

    def test__put__ok(self):
        """Should return a Submission object."""
        fixture = submissions_data.test_submissions
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            with Client() as client:
                # Specify project
                observed = client.submissions._put(
                    project_id=fixture["project_id"],
                    form_id=fixture["form_id"],
                    instance_id=fixture["response_data"][0]["instanceId"],
                    xml=submissions_data.test_xml,
                )
                self.assertIsInstance(observed, Submission)
                # Use default
                observed = client.submissions._put(
                    form_id=fixture["form_id"],
                    instance_id=fixture["response_data"][0]["instanceId"],
                    xml=submissions_data.test_xml,
                )
                self.assertIsInstance(observed, Submission)

    def test_review__ok(self):
        """Should return a Submission object."""
        fixture = submissions_data.test_submissions
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            with Client() as client:
                # Specify project
                observed = client.submissions._patch(
                    project_id=fixture["project_id"],
                    form_id=fixture["form_id"],
                    instance_id=fixture["response_data"][0]["instanceId"],
                    review_state="edited",
                )
                self.assertIsInstance(observed, Submission)
                # Use default
                observed = client.submissions._patch(
                    form_id=fixture["form_id"],
                    instance_id=fixture["response_data"][0]["instanceId"],
                    review_state="edited",
                )
                self.assertIsInstance(observed, Submission)


@patch("pyodk._utils.session.Auth.login", MagicMock())
@patch("pyodk._utils.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestSubmissionAttachments(TestCase):
    def test_list__ok(self):
        """Should return a list of SubmissionAttachment objects."""
        fixture = submission_attachments_data.test_submission_attachments
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture
            with Client() as client:
                observed = client.submission_attachments.list(
                    instance_id="test_submission",
                    form_id="test_form",
                    project_id=1,
                )
        self.assertEqual(len(fixture), len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, SubmissionAttachment)
                self.assertEqual(fixture[i]["name"], o.name)
                self.assertEqual(fixture[i]["exists"], o.exists)

    def test_get__ok(self):
        """Should return the binary content of a submission attachment."""
        fixture = submission_attachments_data.test_submission_attachment_get
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.content = fixture["content"]
            with Client() as client:
                observed = client.submission_attachments.get(
                    file_name=fixture["file_name"],
                    instance_id=fixture["instance_id"],
                    form_id=fixture["form_id"],
                    project_id=fixture["project_id"],
                )
        self.assertEqual(fixture["content"], observed)
        self.assertIsInstance(observed, bytes)

    def test_upload_bytes__ok(self):
        """Should return True when the bytes attachment is successfully uploaded."""
        fixture = submission_attachments_data.test_submission_attachment_upload
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = {"success": True}
            with Client() as client:
                observed = client.submission_attachments.upload(
                    file_path_or_bytes=fixture["file_path_or_bytes"],
                    instance_id=fixture["instance_id"],
                    file_name=fixture["file_name"],
                    form_id=fixture["form_id"],
                    project_id=fixture["project_id"],
                )
        self.assertTrue(observed)

    def test_upload_bytes__no_filename(self):
        """Should return False when no filename is passed uploading bytes."""
        fixture = submission_attachments_data.test_submission_attachment_upload
        with self.assertRaises(PyODKError) as context:
            with patch.object(Session, "request") as mock_session:
                mock_session.return_value.status_code = 200
                mock_session.return_value.json.return_value = {"success": False}
                with Client() as client:
                    client.submission_attachments.upload(
                        file_path_or_bytes=fixture["file_path_or_bytes"],
                        instance_id=fixture["instance_id"],
                        file_name=None,
                        form_id=fixture["form_id"],
                        project_id=fixture["project_id"],
                    )
        self.assertIn("file_name: str type expected", str(context.exception))

    def test_upload_file__ok(self):
        """Should return True when the file attachment is successfully uploaded."""
        fixture = submission_attachments_data.test_submission_attachment_upload
        submission_file_path = (
            RESOURCES / "attachments" / "submission_image.png"
        ).as_posix()
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = {"success": True}
            with Client() as client:
                # Perform the upload action, passing the file path directly
                observed = client.submission_attachments.upload(
                    file_path_or_bytes=submission_file_path,
                    instance_id=fixture["instance_id"],
                    file_name=fixture["file_name"],
                    form_id=fixture["form_id"],
                    project_id=fixture["project_id"],
                )
            self.assertTrue(observed)

    def test_upload_file__not_exist(self):
        """Should return False when attempting upload of non-existent file."""
        fixture = submission_attachments_data.test_submission_attachment_upload
        with self.assertRaises(PyODKError) as context:
            with patch.object(Session, "request") as mock_session:
                mock_session.return_value.status_code = 200
                mock_session.return_value.json.return_value = {"success": False}
                with Client() as client:
                    client.submission_attachments.upload(
                        file_path_or_bytes="/file/path/does/not/exist.jpg",
                        instance_id=fixture["instance_id"],
                        file_name=None,
                        form_id=fixture["form_id"],
                        project_id=fixture["project_id"],
                    )
        self.assertIn("file_path: file or directory at path", str(context.exception))
        # NOTE we avoid checking the path in the exception, due to differences on Windows/Linux
        self.assertIn("does not exist", str(context.exception))
