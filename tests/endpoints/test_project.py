from unittest import TestCase
from unittest.mock import MagicMock, patch

from requests import Session

from pyodk.client import Client
from pyodk.endpoints.project import ProjectEntity
from tests.resources import CONFIG_DATA, project_data


@patch("pyodk.client.Client._login", MagicMock())
@patch("pyodk.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestProject(TestCase):
    def test_read_all__ok(self):
        """Should return a list of ProjectEntity objects."""
        fixture = project_data.test_projects
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture
            with Client() as client:
                observed = client.project.read_all()
        self.assertEqual(2, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, ProjectEntity)

    def test_read__ok(self):
        """Should return a ProjectEntity object."""
        fixture = project_data.test_projects[0]
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture
            with Client() as client:
                # Specify project
                observed = client.project.read(project_id=fixture["id"])
                self.assertIsInstance(observed, ProjectEntity)
                # Use default
                observed = client.project.read()
                self.assertIsInstance(observed, ProjectEntity)
