from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.entity_lists import EntityList
from pyodk._utils.session import Session
from pyodk.client import Client

from tests.resources import CONFIG_DATA, entity_lists_data


@patch("pyodk._utils.session.Auth.login", MagicMock())
@patch("pyodk._utils.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestEntityLists(TestCase):
    def test_list__ok(self):
        """Should return a list of EntityList objects."""
        fixture = entity_lists_data.test_entity_lists
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture
            with Client() as client:
                observed = client.entity_lists.list()
        self.assertEqual(3, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, EntityList)

    def test_get__ok(self):
        """Should an EntityList object."""
        fixture = entity_lists_data.test_entity_lists[2]
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture
            with Client() as client:
                observed = client.entity_lists.get(entity_list_name="pyodk_test_eln")
                self.assertIsInstance(observed, EntityList)

    def test_create__ok(self):
        """Should return an EntityList object."""
        fixture = entity_lists_data.test_entity_lists
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture[0]
            with Client() as client:
                # Specify project
                observed = client.entity_lists.create(
                    project_id=2,
                    entity_list_name="test",
                    approval_required=False,
                )
                self.assertIsInstance(observed, EntityList)
                # Use default
                client.entity_lists.default_entity_list_name = "test"
                client.entity_lists.default_project_id = 2
                observed = client.entity_lists.create()
                self.assertIsInstance(observed, EntityList)
