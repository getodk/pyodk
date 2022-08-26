from unittest import TestCase
from unittest.mock import MagicMock, patch

from requests import Session

from pyodk.client import Client
from pyodk.project import ProjectEntity
from tests.resources import CONFIG_DATA, project_data


@patch("pyodk.client.Client._login", MagicMock())
@patch("pyodk.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestProject(TestCase):
    def test_read_all__ok(self):
        """Should return a list of ProjectEntity objects."""
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = project_data.test_projects
            with Client() as client:
                projects = client.project.read_all()
        self.assertEqual(2, len(projects))
        for i, p in enumerate(projects):
            with self.subTest(i):
                self.assertIsInstance(p, ProjectEntity)

    def test_read__ok(self):
        """Should return a ProjectEntity object."""
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = project_data.test_projects[0]
            with Client() as client:
                project = client.project.read()
        self.assertIsInstance(project, ProjectEntity)
