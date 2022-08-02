import json
import os
from pathlib import Path
from typing import Any, Dict

from pyodk.errors import PyODKError

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


defaults = {
    "PYODK_USERNAME": None,
    "PYODK_PASSWORD": None,
    "PYODK_CONFIG_FILE": Path.home() / ".pyodk_config.toml",
    "PYODK_CACHE_FILE": Path.home() / ".pyodk_cache.json",
}


def get_config_path():
    file_path = defaults["PYODK_CONFIG_FILE"]
    env_file_path = os.environ.get("PYODK_CONFIG_FILE")
    if env_file_path is not None:
        file_path = Path(env_file_path)
    return file_path


def read_config() -> Dict[str, Any]:
    file_path = get_config_path()
    if not (file_path.exists() and file_path.is_file()):
        raise PyODKError("Config file does not exist.")
    with open(file_path, "rb") as f:
        return tomllib.load(f)


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
            cache = json.load(cache_file)
            return cache["token"]
    except (FileNotFoundError, KeyError) as err:
        raise PyODKError("Could not read cached token.") from err


def write_cache(key: str, value: str):
    """
    Append or overwrite the given key/value pair to the cache file.
    """
    file_path = get_cache_path()
    try:
        with open(file_path, "r") as file:
            cache = json.load(file)
            cache[key] = value
    except FileNotFoundError:
        cache = {key: value}

    with open(file_path, "w") as outfile:
        json.dump(cache, outfile)
