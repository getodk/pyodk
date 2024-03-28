from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.entities import Entity
from pyodk._utils.session import Session
from pyodk.client import Client

from tests.resources import CONFIG_DATA, entities_data


@patch("pyodk._utils.session.Auth.login", MagicMock())
@patch("pyodk._utils.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestEntities(TestCase):
    def test_list__ok(self):
        """Should return a list of Entity objects."""
        fixture = entities_data.test_entities
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture
            with Client() as client:
                observed = client.entities.list(entity_list_name="test")
        self.assertEqual(2, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, Entity)

    def test_create__ok(self):
        """Should return an Entity object."""
        fixture = entities_data.test_entities
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture[0]
            with Client() as client:
                # Specify project
                observed = client.entities.create(
                    project_id=2,
                    entity_list_name="test",
                    label="John (88)",
                    data=entities_data.test_entities_data,
                )
                self.assertIsInstance(observed, Entity)
                # Use default
                observed = client.entities.create(
                    entity_list_name="test",
                    label="John (88)",
                    data=entities_data.test_entities_data,
                )
                self.assertIsInstance(observed, Entity)
