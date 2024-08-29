from csv import DictReader
from io import StringIO
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyodk._endpoints.entities import Entity, MergeActions
from pyodk._endpoints.entities import EntityService as es
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


class TestPrepDataForMerge(TestCase):
    def test_noop__source_same_as_target(self):
        """Should identify no rows for insert/update/delete"""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        target = source
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual({}, observed.to_update, observed.to_update)
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state", "postcode"}, observed.target_keys)

    def test_noop__source_has_no_value_for_key(self):
        """Should identify no rows for insert/update/delete"""
        source = [
            {"label": "Sydney", "state": "NSW"},
        ]
        target = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual({}, observed.to_update, observed.to_update)
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state"}, observed.source_keys)
        self.assertEqual({"label", "state", "postcode"}, observed.target_keys)

    def test_to_insert__source_has_new_row__empty(self):
        """Should identify row to_insert only."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        target = []
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_insert.keys()))[0],
            observed.to_insert,
        )
        self.assertEqual({}, observed.to_update, observed.to_update)
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual(set(), observed.target_keys)

    def test_to_insert__source_has_new_row__existing(self):
        """Should identify row to_insert only."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
            {"label": "Brisbane", "state": "QLD", "postcode": "4000"},
        ]
        target = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual(
            source[1]["label"],
            next(iter(observed.to_insert.keys()))[0],
            observed.to_insert,
        )
        self.assertEqual({}, observed.to_update, observed.to_update)
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state", "postcode"}, observed.target_keys)

    def test_to_delete__target_has_extra_row__empty(self):
        """Should identify row to_delete only."""
        source = []
        target = [
            {"label": "Sydney", "state": "VIC", "postcode": "2000"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual({}, observed.to_update, observed.to_update)
        self.assertEqual(
            target[0]["label"],
            next(iter(observed.to_delete.keys()))[0],
            observed.to_delete,
        )
        self.assertEqual(set(), observed.source_keys)
        self.assertEqual({"label", "state", "postcode"}, observed.target_keys)

    def test_to_delete__target_has_extra_row__existing(self):
        """Should identify row to_delete only."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        target = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
            {"label": "Brisbane", "state": "QLD", "postcode": "4000"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual({}, observed.to_update, observed.to_update)
        self.assertEqual(
            target[1]["label"],
            next(iter(observed.to_delete.keys()))[0],
            observed.to_delete,
        )
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state", "postcode"}, observed.target_keys)

    def test_to_update__source_value_changed__from_existing(self):
        """Should identify row to_update only."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        target = [
            {"label": "Sydney", "state": "NSW", "postcode": "3000"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state", "postcode"}, observed.target_keys)

    def test_to_update__source_value_changed__from_none(self):
        """Should identify row to_update only."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        target = [
            {"label": "Sydney", "state": "NSW", "postcode": None},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state", "postcode"}, observed.target_keys)

    def test_to_update__source_value_changed__to_none(self):
        """Should identify row to_update only."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": None},
        ]
        target = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state", "postcode"}, observed.target_keys)

    def test_to_update__new_source_field(self):
        """Should identify row to_update only."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        target = [
            {"label": "Sydney", "state": "NSW"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state"}, observed.target_keys)

    def test_to_update__new_source_field__with_other_change(self):
        """Should identify row to_update only."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        target = [
            {"label": "Sydney", "state": "QLD"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state"}, observed.target_keys)

    def test_to_update__new_source_field__with_no_old_data(self):
        """Should identify row to_update only."""
        source = [
            {"label": "Sydney", "postcode": "2000"},
        ]
        target = [
            {"label": "Sydney", "state": "NSW"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual({}, observed.to_insert, observed.to_insert)
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual({}, observed.to_delete, observed.to_delete)
        self.assertEqual({"label", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state"}, observed.target_keys)

    def test_merge__all_ops(self):
        """Should identify a row for each op type at the same time."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},  # update
            {"label": "Brisbane", "state": "QLD", "postcode": "4000"},  # insert
            {"label": "Melbourne", "state": "VIC"},  # noop
        ]
        target = [
            {"label": "Sydney", "state": "VIC"},
            {"label": "Darwin", "state": "NT"},  # delete
            {"label": "Melbourne", "state": "VIC"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertIsInstance(observed, MergeActions)
        self.assertEqual(1, len(observed.to_insert))
        self.assertEqual(
            source[1]["label"],
            next(iter(observed.to_insert.keys()))[0],
            observed.to_insert,
        )
        self.assertEqual(1, len(observed.to_update))
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual(1, len(observed.to_delete))
        self.assertEqual(
            target[1]["label"],
            next(iter(observed.to_delete.keys()))[0],
            observed.to_delete,
        )
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state"}, observed.target_keys)

    def test_merge__all_ops__alternative_source_label_key(self):
        """Should identify a row for each op type at the same time."""
        source = [
            {"city": "Sydney", "state": "NSW", "postcode": "2000"},  # update
            {"city": "Brisbane", "state": "QLD", "postcode": "4000"},  # insert
            {"city": "Melbourne", "state": "VIC"},  # noop
        ]
        target = [
            {"label": "Sydney", "state": "VIC"},
            {"label": "Darwin", "state": "NT"},  # delete
            {"label": "Melbourne", "state": "VIC"},
        ]
        observed = es._prep_data_for_merge(
            source_data=source, target_data=target, source_label_key="city"
        )
        self.assertEqual(1, len(observed.to_insert))
        self.assertEqual(
            source[1]["city"],
            next(iter(observed.to_insert.keys()))[0],
            observed.to_insert,
        )
        self.assertEqual(1, len(observed.to_update))
        self.assertEqual(
            source[0]["city"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual(1, len(observed.to_delete))
        self.assertEqual(
            target[1]["label"],
            next(iter(observed.to_delete.keys()))[0],
            observed.to_delete,
        )
        self.assertEqual({"label", "state", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "state"}, observed.target_keys)

    def test_merge__all_ops__source_data_not_strings(self):
        """Should identify a row for each op type at the same time."""
        source = [
            {"label": "Sydney", "postcode": 2000},  # update
            {"label": "Brisbane", "postcode": 4000},  # insert
            {"label": "Melbourne", "postcode": 3000},  # noop
        ]
        target = [
            {"label": "Sydney", "postcode": "3000"},
            {"label": "Darwin", "postcode": "4000"},  # delete
            {"label": "Melbourne", "postcode": "3000"},
        ]
        observed = es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual(1, len(observed.to_insert))
        self.assertEqual(
            source[1]["label"],
            next(iter(observed.to_insert.keys()))[0],
            observed.to_insert,
        )
        self.assertEqual(1, len(observed.to_update))
        self.assertEqual(
            source[0]["label"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual(1, len(observed.to_delete))
        self.assertEqual(
            target[1]["label"],
            next(iter(observed.to_delete.keys()))[0],
            observed.to_delete,
        )
        self.assertEqual({"label", "postcode"}, observed.source_keys)
        self.assertEqual({"label", "postcode"}, observed.target_keys)

    def test_merge__all_ops__match_keys_not_including_label(self):
        """Should identify a row for each op type at the same time."""
        source = [
            {"label": "Sydney", "id": "2", "state": "NSW", "postcode": "2000"},  # update
            {
                "label": "Brisbane",
                "id": "4",
                "state": "QLD",
                "postcode": "4000",
            },  # insert
            {"label": "Melbourne", "id": "3", "state": "VIC"},  # noop
        ]
        target = [
            {"label": "Sydney", "id": "2", "state": "VIC"},
            {"label": "Darwin", "id": "1", "state": "NT"},  # delete
            {"label": "Melbourne", "id": "3", "state": "VIC"},
        ]
        observed = es._prep_data_for_merge(
            source_data=source, target_data=target, match_keys=("id",)
        )
        self.assertEqual(1, len(observed.to_insert))
        self.assertEqual(
            source[1]["id"],
            next(iter(observed.to_insert.keys()))[0],
            observed.to_insert,
        )
        self.assertEqual(1, len(observed.to_update))
        self.assertEqual(
            source[0]["id"],
            next(iter(observed.to_update.keys()))[0],
            observed.to_update,
        )
        self.assertEqual(1, len(observed.to_delete))
        self.assertEqual(
            target[1]["id"],
            next(iter(observed.to_delete.keys()))[0],
            observed.to_delete,
        )
        self.assertEqual({"id", "label", "postcode", "state"}, observed.source_keys)
        self.assertEqual({"id", "label", "state"}, observed.target_keys)

    def test_source_has_duplicate_match_key(self):
        """Should detect duplicate rows in source."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
        ]
        target = []
        with self.assertRaises(PyODKError) as err:
            es._prep_data_for_merge(source_data=source, target_data=target)
        self.assertEqual(
            "Parameter 'match_keys' not unique across all 'source_data'.",
            err.exception.args[0],
        )

    def test_source_has_row_missing_match_key(self):
        """Should detect rows in source missing a match key."""
        source = [
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
            {"label": "Brisbane", "postcode": "4000"},
        ]
        target = []
        with self.assertRaises(PyODKError) as err:
            es._prep_data_for_merge(
                source_data=source, target_data=target, match_keys={"label", "state"}
            )
        self.assertEqual(
            "Found Entity that did not have all expected match_keys: 'state'",
            err.exception.args[0],
        )

    def test_source_keys_limits_columns_of_interest(self):
        """Should only process source_keys if specified."""
        source = [
            {"city": "Sydney", "state": "NSW", "postcode": "2000"},
            {"city": "Brisbane", "state": "QLD", "postcode": "4000"},
            {"city": "Hobart"},
        ]
        target = [
            {"label": "Sydney", "state": "VIC", "postcode": "3000"},
            {"label": "Brisbane", "state": "QLD"},
            {"label": "Hobart"},
        ]
        observed = es._prep_data_for_merge(
            source_data=source,
            target_data=target,
            source_label_key="city",
            source_keys={"city", "state"},
        )
        # "city" is translated to "label", "postcode" is ignored, "state" is updated.
        self.assertEqual(1, len(observed.to_update))
        self.assertEqual(
            {"label": "Sydney", "state": "NSW"},
            next(iter(observed.to_update.values())),
            observed.to_update,
        )
        self.assertEqual(0, len(observed.to_insert))
        self.assertEqual(0, len(observed.to_delete))
        self.assertEqual(["label"], observed.match_keys)

    def test_source_keys_does_not_include_label_or_source_label_key(self):
        """Should raise an error if the source column specifications don't make sense."""
        source = [
            {"city": "Sydney", "state": "NSW", "postcode": "2000"},
            {"city": "Brisbane", "postcode": "4000"},
        ]
        target = []
        with self.assertRaises(PyODKError) as err:
            es._prep_data_for_merge(
                source_data=source,
                target_data=target,
                source_label_key="city",
                source_keys={"state", "postcode"},
            )
        self.assertEqual(
            "Parameter 'source_keys' must include \"label\" or the "
            "'source_label_key' parameter value",
            err.exception.args[0],
        )

    def test_csv_as_source_data(self):
        """Should be able to pass in CSV DictReader as a the source_data."""
        csv = """label,state,postcode\nSydney,NSW,2000\nBrisbane,QLD,4000"""
        target = [{"label": "Brisbane", "state": "QLD", "postcode": "4000"}]
        observed = es._prep_data_for_merge(
            source_data=list(DictReader(StringIO(csv))),
            target_data=target,
        )
        self.assertEqual(1, len(observed.to_insert))
        self.assertEqual(
            {"label": "Sydney", "state": "NSW", "postcode": "2000"},
            next(iter(observed.to_insert.values())),
        )
        self.assertEqual(0, len(observed.to_update))
        self.assertEqual(0, len(observed.to_delete))
