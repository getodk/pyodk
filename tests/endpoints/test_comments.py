from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk.client import Client
from pyodk.endpoints.comment import Comment
from pyodk.session import Session
from tests.resources import CONFIG_DATA, comments_data


@patch("pyodk.client.Client._login", MagicMock())
@patch("pyodk.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestComments(TestCase):
    def test_list__ok(self):
        """Should return a list of Comment objects."""
        fixture = comments_data.test_comments
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"]
            with Client() as client:
                observed = client.comments.list(
                    form_id=fixture["form_id"],
                    instance_id=fixture["instance_id"],
                )
        self.assertEqual(4, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, Comment)

    def test_post__ok(self):
        """Should return a Comment object."""
        fixture = comments_data.test_comments
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            with Client() as client:
                # Specify project
                observed = client.comments.post(
                    project_id=fixture["project_id"],
                    form_id=fixture["form_id"],
                    instance_id=fixture["instance_id"],
                    comment="Looks good",
                )
                self.assertIsInstance(observed, Comment)
                # Use default
                observed = client.comments.post(
                    form_id=fixture["form_id"],
                    instance_id=fixture["instance_id"],
                    comment="Looks good",
                )
                self.assertIsInstance(observed, Comment)
