from collections.abc import Callable
from os import PathLike
from pathlib import Path
from typing import Any

from pydantic.v1 import validators as v
from pydantic.v1.errors import PydanticTypeError, PydanticValueError

from pyodk._utils.utils import coalesce
from pyodk.errors import PyODKError


def wrap_error(validator: Callable, key: str, value: Any) -> Any:
    """
    Wrap the error in a PyODKError, with a nicer message.

    :param validator: A pydantic validator function.
    :param key: The variable name to use in the error message.
    :param value: The variable value.
    :return:
    """
    try:
        return validator(value)
    except (PydanticTypeError, PydanticValueError) as err:
        msg = f"{key}: {err!s}"
        raise PyODKError(msg) from err


def validate_project_id(*args: int) -> int:
    return wrap_error(
        validator=v.int_validator,
        key="project_id",
        value=coalesce(*args),
    )


def validate_form_id(*args: str) -> str:
    return wrap_error(
        validator=v.str_validator,
        key="form_id",
        value=coalesce(*args),
    )


def validate_table_name(*args: str) -> str:
    return wrap_error(
        validator=v.str_validator,
        key="table_name",
        value=coalesce(*args),
    )


def validate_instance_id(*args: str) -> str:
    return wrap_error(
        validator=v.str_validator,
        key="instance_id",
        value=coalesce(*args),
    )


def validate_entity_list_name(*args: str) -> str:
    return wrap_error(
        validator=v.str_validator,
        key="entity_list_name",
        value=coalesce(*args),
    )


def validate_str(*args: str | None, key: str) -> str:
    return wrap_error(
        validator=v.str_validator,
        key=key,
        value=coalesce(*args),
    )


def validate_bool(*args: bool, key: str) -> str:
    return wrap_error(
        validator=v.bool_validator,
        key=key,
        value=coalesce(*args),
    )


def validate_int(*args: int, key: str) -> int:
    return wrap_error(
        validator=v.int_validator,
        key=key,
        value=coalesce(*args),
    )


def validate_dict(*args: dict, key: str) -> int:
    return wrap_error(
        validator=v.dict_validator,
        key=key,
        value=coalesce(*args),
    )


def validate_file_path(*args: PathLike | str, key: str = "file_path") -> Path:
    def validate_fp(f):
        p = v.path_validator(f)
        return v.path_exists_validator(p)

    return wrap_error(validator=validate_fp, key=key, value=coalesce(*args))


def validate_is_instance(*args: Any, typ: Any, key: str):
    val = coalesce(*args)
    if not isinstance(val, typ):
        raise PyODKError(f"{key}: Unexpected type. Expected '{typ}'.")
    return val
