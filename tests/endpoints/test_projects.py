from unittest import TestCase
from unittest.mock import MagicMock, patch

from requests import Session

from pyodk.client import Client
from pyodk.endpoints.projects import Project
from tests.resources import CONFIG_DATA, projects_data


@patch("pyodk.client.Client._login", MagicMock())
@patch("pyodk.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestProjects(TestCase):
    def test_read_all__ok(self):
        """Should return a list of ProjectType objects."""
        fixture = projects_data.test_projects
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"]
            with Client() as client:
                observed = client.projects.read_all()
        self.assertEqual(2, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, Project)

    def test_read__ok(self):
        """Should return a ProjectType object."""
        fixture = projects_data.test_projects
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture["response_data"][0]
            with Client() as client:
                # Specify project
                observed = client.projects.read(
                    project_id=fixture["response_data"][0]["id"]
                )
                self.assertIsInstance(observed, Project)
                # Use default
                observed = client.projects.read()
                self.assertIsInstance(observed, Project)
