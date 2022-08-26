from pathlib import Path

from toml import load

from tests.resources import form_data  # noqa: F401
from tests.resources import project_data  # noqa: F401

RESOURCES = Path.absolute(Path(__file__)).parent

CONFIG_FILE = RESOURCES / ".pyodk_config.toml"
CONFIG_DATA = load(CONFIG_FILE)
