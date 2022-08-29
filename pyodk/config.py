import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import toml

from pyodk.errors import PyODKError

log = logging.getLogger(__name__)

defaults = {
    "PYODK_CONFIG_FILE": Path.home() / ".pyodk_config.toml",
    "PYODK_CACHE_FILE": Path.home() / ".pyodk_cache.toml",
}


@dataclass
class CentralConfig:

    base_url: str
    username: str
    password: str = field(repr=False)
    default_project_id: Optional[int] = None

    def validate(self):
        for key in ["base_url", "username", "password"]:  # Mandatory keys.
            if getattr(self, key) is None or getattr(self, key) == "":
                err = PyODKError(f"Config value '{key}' must not be empty.")
                log.error(err, exc_info=True)
                raise err

    def __post_init__(self):
        self.validate()


@dataclass
class Config:
    central: CentralConfig


def objectify_config(config_data: Dict) -> Config:
    """
    Convert a config dict into objects to validate the data.
    """
    central = CentralConfig(**config_data["central"])
    config = Config(central=central)
    return config


def get_config_path():
    file_path = defaults["PYODK_CONFIG_FILE"]
    env_file_path = os.environ.get("PYODK_CONFIG_FILE")
    if env_file_path is not None:
        file_path = Path(env_file_path)
    return file_path


def read_config() -> Config:
    file_path = get_config_path()
    if not (file_path.exists() and file_path.is_file()):
        err = PyODKError(f"Config file does not exist, expected at: {file_path}")
        log.error(err, exc_info=True)
        raise err
    with open(file_path, "r") as f:
        config_data = toml.load(f)
    return objectify_config(config_data=config_data)


def get_cache_path():
    file_path = defaults["PYODK_CACHE_FILE"]
    env_file_path = os.environ.get("PYODK_CACHE_FILE")
    if env_file_path is not None:
        file_path = Path(env_file_path)
    return file_path


def read_cache_token() -> str:
    file_path = get_cache_path()
    try:
        with open(file_path, "r") as cache_file:
            cache = toml.load(cache_file)
            return cache["token"]
    except (FileNotFoundError, KeyError) as err:
        err = PyODKError(f"Could not read cached token: {repr(err)}.")
        log.error(err, exc_info=True)
        raise err


def write_cache(key: str, value: str):
    """
    Append or overwrite the given key/value pair to the cache file.
    """
    file_path = get_cache_path()
    try:
        with open(file_path, "r") as file:
            cache = toml.load(file)
            cache[key] = value
    except FileNotFoundError:
        cache = {key: value}

    with open(file_path, "w") as outfile:
        toml.dump(cache, outfile)


def delete_cache():
    """Delete the cache file, if it exists."""
    file_path = get_cache_path()
    Path.unlink(file_path, missing_ok=True)
