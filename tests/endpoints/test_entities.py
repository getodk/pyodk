from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.entities import Entity
from pyodk._utils.session import Session
from pyodk.client import Client
from pyodk.errors import PyODKError

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

    def test_update__ok(self):
        """Should return an Entity object."""
        fixture = entities_data.test_entities
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            for i, case in enumerate(fixture):
                with self.subTest(msg=f"Case: {i}"):
                    mock_session.return_value.json.return_value = case
                    with Client() as client:
                        force = None
                        base_version = case["currentVersion"]["baseVersion"]
                        if base_version is None:
                            force = True
                        # Specify project
                        observed = client.entities.update(
                            project_id=2,
                            entity_list_name="test",
                            label=case["currentVersion"]["label"],
                            data=entities_data.test_entities_data,
                            uuid=case["uuid"],
                            base_version=base_version,
                            force=force,
                        )
                        self.assertIsInstance(observed, Entity)
                        # Use default
                        client.entities.default_entity_list_name = "test"
                        observed = client.entities.update(
                            label=case["currentVersion"]["label"],
                            data=entities_data.test_entities_data,
                            uuid=case["uuid"],
                            base_version=base_version,
                            force=force,
                        )
                        self.assertIsInstance(observed, Entity)

    def test_update__raise_if_invalid_force_or_base_version(self):
        """Should raise an error for invalid `force` or `base_version` specification."""
        fixture = entities_data.test_entities
        with patch.object(Session, "request") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture[1]
            with Client() as client:
                with self.assertRaises(PyODKError) as err:
                    client.entities.update(
                        project_id=2,
                        entity_list_name="test",
                        uuid=fixture[1]["uuid"],
                        label=fixture[1]["currentVersion"]["label"],
                        data=entities_data.test_entities_data,
                    )
                    self.assertIn(
                        "Must specify one of 'force' or 'base_version'.",
                        err.exception.args[0],
                    )
                with self.assertRaises(PyODKError) as err:
                    client.entities.update(
                        project_id=2,
                        entity_list_name="test",
                        uuid=fixture[1]["uuid"],
                        label=fixture[1]["currentVersion"]["label"],
                        data=entities_data.test_entities_data,
                        force=True,
                        base_version=fixture[1]["currentVersion"]["baseVersion"],
                    )
                    self.assertIn(
                        "Must specify one of 'force' or 'base_version'.",
                        err.exception.args[0],
                    )
