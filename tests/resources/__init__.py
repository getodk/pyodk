from pathlib import Path

from toml import load

from pyodk import config
from tests.resources import forms_data  # noqa: F401
from tests.resources import projects_data  # noqa: F401

RESOURCES = Path.absolute(Path(__file__)).parent

CONFIG_FILE = RESOURCES / ".pyodk_config.toml"
CONFIG_DATA = config.objectify_config(load(CONFIG_FILE))
