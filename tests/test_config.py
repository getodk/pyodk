import os
from unittest import TestCase
from unittest.mock import patch

from pyodk._utils import config
from pyodk.errors import PyODKError

from tests import resources
from tests.utils.utils import get_temp_dir


class TestConfig(TestCase):
    def setUp(self) -> None:
        self.section_data = {
            "base_url": "https://www.example.com",
            "username": "user",
            "password": "pass",
        }

    def test_read_config__ok(self):
        """Should return the configuration data when no path is specified."""
        cf = {"PYODK_CONFIG_FILE": resources.CONFIG_FILE.as_posix()}
        with patch.dict(os.environ, cf, clear=True):
            self.assertIsInstance(config.read_config(), config.Config)

    def test_read_config__ok__with_path(self):
        """Should return the configuration data when a path is specified."""
        self.assertIsInstance(
            config.read_config(config_path=resources.CONFIG_FILE), config.Config
        )

    def test_read_cache__ok(self):
        """Should return the cache data when no path is specified."""
        cf = {"PYODK_CACHE_FILE": resources.CACHE_FILE.as_posix()}
        with patch.dict(os.environ, cf, clear=True):
            self.assertIsInstance(config.read_cache_token(), str)

    def test_read_cache__ok__with_path(self):
        """Should return the cache data when a path is specified."""
        self.assertIsInstance(
            config.read_cache_token(cache_path=resources.CACHE_FILE), str
        )

    def test_read_toml__error__non_existent(self):
        """Should raise an error if the path is not valid."""
        bad_path = resources.RESOURCES / "nothing_here"
        with self.assertRaises(PyODKError) as err:
            config.read_toml(path=bad_path)
        self.assertTrue(
            str(err.exception.args[0]).startswith(f"Could not read file at: {bad_path}")
        )

    def test_write_cache__ok(self):
        """Should write the cache data when no path is specified."""
        with get_temp_dir() as tmp:
            path = tmp / "my_cache.toml"
            with patch.dict(os.environ, {"PYODK_CACHE_FILE": path.as_posix()}):
                self.assertFalse(path.exists())
                config.write_cache(key="token", value="1234abcd")
                self.assertTrue(path.exists())

    def test_write_cache__with_path(self):
        """Should write the cache data when a path is specified."""
        with get_temp_dir() as tmp:
            path = tmp / "my_cache.toml"
            self.assertFalse(path.exists())
            config.write_cache(key="token", value="1234abcd", cache_path=path.as_posix())
            self.assertTrue(path.exists())

    def test_objectify_config__error__missing_section(self):
        cfg = {"centrall": {}}
        with self.assertRaises(KeyError) as err:
            config.objectify_config(config_data=cfg)
        self.assertEqual("central", err.exception.args[0])

    def test_objectify_config__error__missing_key(self):
        del self.section_data["password"]
        cfg = {"central": self.section_data}
        with self.assertRaises(TypeError) as err:
            config.objectify_config(config_data=cfg)
        # Py3.8 doesn't prefix the class name to __init__(), but Py3.10 does.
        self.assertIn(
            "__init__() missing 1 required positional argument: 'password'",
            err.exception.args[0],
        )

    def test_objectify_config__error__empty_key(self):
        self.section_data["password"] = ""
        cfg = {"central": self.section_data}
        with self.assertRaises(PyODKError) as err:
            config.objectify_config(config_data=cfg)
        self.assertEqual(
            "Config value 'password' must not be empty.", err.exception.args[0]
        )

    def test_read_envvars____ok__required_vars_present(self):
        """Successfully reads environment variables as PyOdk config."""
        cfg = {
            "PYODK_CENTRAL_URL": "https://env.vars.config.com",
            "PYODK_CENTRAL_USER": "user@env.vars.config.com",
            "PYODK_CENTRAL_PASS": "DifferentPassword",
        }

        with patch.dict(os.environ, cfg, clear=True):
            new_config = config.read_config()
            self.assertEqual(new_config.central.base_url, cfg["PYODK_CENTRAL_URL"])
            self.assertEqual(new_config.central.username, cfg["PYODK_CENTRAL_USER"])
            self.assertEqual(new_config.central.password, cfg["PYODK_CENTRAL_PASS"])

    def test_read_envvars__error_missing_required_env_var(self):
        """Raise an error when no config is provided and required env vars are missing."""
        cfg = {
            "PYODK_CENTRAL_USER": "https://env.vars.config.com",
            "PYODK_CENTRAL_PASS": "user@env.vars.config.com",
            # Missing PYODK_CENTRAL_URL
        }
        with patch.dict(os.environ, cfg, clear=True):
            with self.assertRaises(PyODKError) as err:
                config.read_config()
            self.assertIn("No valid configuration found", str(err.exception))

    def test_read_envvars__ok__with_empty_default_project_id(self):
        """All required env vars are set, but PYODK_DEFAULT_PROJECT_ID is empty string."""
        cfg = {
            "PYODK_CENTRAL_URL": "https://env.vars.config.com",
            "PYODK_CENTRAL_USER": "user@env.vars.config.com",
            "PYODK_CENTRAL_PASS": "DifferentPassword",
            "PYODK_DEFAULT_PROJECT_ID": "",  # Empty string should be ignored
        }
        with patch.dict(os.environ, cfg, clear=True):
            conf = config.read_config()
            self.assertEqual(conf.central.base_url, cfg["PYODK_CENTRAL_URL"])
            self.assertEqual(conf.central.username, cfg["PYODK_CENTRAL_USER"])
            self.assertEqual(conf.central.password, cfg["PYODK_CENTRAL_PASS"])
            self.assertEqual(conf.central.default_project_id, None)

    def test_read_envvars__ok__with_valid_default_project_id(self):
        """Return config and include PYODK_DEFAULT_PROJECT_ID when it is provided."""
        cfg = {
            "PYODK_CENTRAL_URL": "https://env.vars.config.com",
            "PYODK_CENTRAL_USER": "user@env.vars.config.com",
            "PYODK_CENTRAL_PASS": "DifferentPassword",
            "PYODK_DEFAULT_PROJECT_ID": "123",
        }
        with patch.dict(os.environ, cfg, clear=True):
            conf = config.read_config()
            self.assertEqual(conf.central.base_url, cfg["PYODK_CENTRAL_URL"])
            self.assertEqual(conf.central.username, cfg["PYODK_CENTRAL_USER"])
            self.assertEqual(conf.central.password, cfg["PYODK_CENTRAL_PASS"])
            self.assertEqual(
                conf.central.default_project_id, cfg["PYODK_DEFAULT_PROJECT_ID"]
            )

    def test_read_config__ok__file_takes_precedence(self):
        """If env vars are present, but a file is specified, it takes precedence."""
        cfg = {
            "PYODK_CENTRAL_URL": "https://env.vars.config.com",
            "PYODK_CENTRAL_USER": "user@env.vars.config.com",
            "PYODK_CENTRAL_PASS": "DifferentPassword",
            "PYODK_DEFAULT_PROJECT_ID": "123",
        }
        with patch.dict(os.environ, cfg, clear=True):
            conf = config.read_config(config_path=resources.CONFIG_FILE)
            # Check the env var values aren't present in config
            self.assertNotEqual(conf.central.base_url, cfg["PYODK_CENTRAL_URL"])
            self.assertNotEqual(conf.central.username, cfg["PYODK_CENTRAL_USER"])
            self.assertNotEqual(conf.central.password, cfg["PYODK_CENTRAL_PASS"])
            self.assertNotEqual(
                conf.central.default_project_id, cfg["PYODK_DEFAULT_PROJECT_ID"]
            )
