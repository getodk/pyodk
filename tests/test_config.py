from unittest import TestCase

from pyodk import config
from pyodk.errors import PyODKError


class TestConfig(TestCase):
    def setUp(self) -> None:
        self.section_data = {
            "base_url": "https://www.example.com",
            "username": "user",
            "password": "pass",
        }

    def test_read_config__ok(self):
        """Should return the configuration data."""
        self.assertIsInstance(config.read_config(), config.Config)

    def test_read_config__error__missing_section(self):
        cfg = {"centrall": {}}
        with self.assertRaises(KeyError) as err:
            config.objectify_config(config_data=cfg)
        self.assertEqual("central", err.exception.args[0])

    def test_read_config__error__missing_key(self):
        del self.section_data["password"]
        cfg = {"central": self.section_data}
        with self.assertRaises(TypeError) as err:
            config.objectify_config(config_data=cfg)
        self.assertEqual(
            "__init__() missing 1 required positional argument: 'password'",
            err.exception.args[0],
        )

    def test_read_config__error__empty_key(self):
        self.section_data["password"] = ""
        cfg = {"central": self.section_data}
        with self.assertRaises(PyODKError) as err:
            config.objectify_config(config_data=cfg)
        self.assertEqual(
            "Config value 'password' must not be empty.", err.exception.args[0]
        )
