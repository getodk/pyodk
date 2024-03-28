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
        self.assertEqual(2, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, EntityList)
