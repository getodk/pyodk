from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.submissions import Submission
from pyodk._utils.session import Session
from pyodk.client import Client
from tests.resources import CONFIG_DATA, submissions_data


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
