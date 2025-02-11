import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

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
    default_project_id: int | None = None

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


def objectify_config(config_data: dict) -> Config:
    """
    Convert a config dict into objects to validate the data.
    """
    central = CentralConfig(**config_data["central"])
    return Config(central=central)


def get_path(path: str, env_key: str) -> Path:
    """
    Get a path from the path argument, the environment key, or the default.
    """
    # Manually specified path
    if path is not None:
        return Path(path)
    env_file_path = os.environ.get(env_key)
    # User specified path from env var
    if env_file_path is not None:
        return Path(env_file_path)
    # Use default ./.pyodk_config.toml
    return defaults[env_key]


def get_config_path(config_path: str | None = None) -> Path:
    return get_path(path=config_path, env_key="PYODK_CONFIG_FILE")


def get_cache_path(cache_path: str | None = None) -> Path:
    return get_path(path=cache_path, env_key="PYODK_CACHE_FILE")


def read_toml(path: Path) -> dict:
    """
    Read a toml file.
    """
    try:
        with open(path) as f:
            return toml.load(f)
    except (FileNotFoundError, PermissionError) as err:
        pyodk_err = PyODKError(f"Could not read file at: {path}. {err!r}.")
        log.error(pyodk_err, exc_info=True)
        raise pyodk_err from err


def read_config(config_path: str | None = None) -> Config:
    """
    Read the config file.
    """
    # Read credentials from config file
    file_path = get_config_path(config_path)
    if file_path.exists():
        file_data = read_toml(file_path)
        return objectify_config(config_data=file_data)

    # Else fallback to environment variables
    env_config = {
        "central": {
            "base_url": os.getenv("PYODK_CENTRAL_URL"),
            "username": os.getenv("PYODK_CENTRAL_USER"),
            "password": os.getenv("PYODK_CENTRAL_PASS"),
        }
    }

    default_project_id = os.getenv("PYODK_DEFAULT_PROJECT_ID")
    if default_project_id:  # Include optional `default_project_id` key, only if it's set
        env_config["central"]["default_project_id"] = default_project_id

    if all(env_config["central"].values()):
        return objectify_config(config_data=env_config)

    # If no configuration, then error
    err_msg = (
        "No valid configuration found. Please provide a config file "
        "or set the required environment variables. "
        "See https://github.com/getodk/pyodk?tab=readme-ov-file#configure for details."
    )
    log.error(err_msg)
    raise PyODKError(err_msg)


def read_cache_token(cache_path: str | None = None) -> str:
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


def write_cache(key: str, value: str, cache_path: str | None = None) -> None:
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


def delete_cache(cache_path: str | None = None) -> None:
    """
    Delete the cache file, if it exists.
    """
    file_path = get_cache_path(cache_path=cache_path)
    file_path.unlink(missing_ok=True)
