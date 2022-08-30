from pathlib import Path

from pyodk import config
from tests.resources import forms_data  # noqa: F401
from tests.resources import projects_data  # noqa: F401

RESOURCES = Path.absolute(Path(__file__)).parent

CONFIG_FILE = RESOURCES / ".pyodk_config.toml"
CONFIG_DATA = config.read_config(config_path=CONFIG_FILE.as_posix())

CACHE_FILE = RESOURCES / ".pyodk_cache.toml"
CACHE_DATA = config.read_cache_token(cache_path=CACHE_FILE.as_posix())
