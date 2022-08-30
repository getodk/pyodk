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


def get_path(path: str, env_key: str) -> Path:
    """
    Get a path from the path argument, the environment key, or the default.
    """
    if path is not None:
        return Path(path)
    env_file_path = os.environ.get(env_key)
    if env_file_path is not None:
        return Path(env_file_path)
    return defaults[env_key]


def get_config_path(config_path: Optional[str] = None) -> Path:
    return get_path(path=config_path, env_key="PYODK_CONFIG_FILE")


def get_cache_path(cache_path: Optional[str] = None) -> Path:
    return get_path(path=cache_path, env_key="PYODK_CACHE_FILE")


def read_toml(path: Path) -> Dict:
    """
    Read a toml file.
    """
    try:
        with open(path, "r") as f:
            return toml.load(f)
    except (FileNotFoundError, PermissionError) as err:
        err = PyODKError(f"Could not read file at: {path}. {repr(err)}.")
        log.error(err, exc_info=True)
        raise err


def read_config(config_path: Optional[str] = None) -> Config:
    """
    Read the config file.
    """
    file_path = get_path(path=config_path, env_key="PYODK_CONFIG_FILE")
    file_data = read_toml(path=file_path)
    return objectify_config(config_data=file_data)


def read_cache_token(cache_path: Optional[str] = None) -> str:
    """
    Read the "token" key from the cache file.
    """
    file_path = get_cache_path(cache_path=cache_path)
    file_data = read_toml(path=file_path)
    if "token" not in file_data:
        err = PyODKError(f"Cached token not found in file: {file_path}")
        log.error(err, exc_info=True)
        raise err
    return file_data["token"]


def write_cache(key: str, value: str, cache_path: Optional[str] = None) -> None:
    """
    Append or overwrite the given key/value pair to the cache file.
    """
    file_path = get_cache_path(cache_path=cache_path)
    if file_path.exists() and file_path.is_file():
        file_data = read_toml(path=file_path)
        file_data[key] = value
    else:
        file_data = {key: value}
    with open(file_path, "w") as outfile:
        toml.dump(file_data, outfile)


def delete_cache(cache_path: Optional[str] = None) -> None:
    """
    Delete the cache file, if it exists.
    """
    file_path = get_cache_path(cache_path=cache_path)
    file_path.unlink(missing_ok=True)
