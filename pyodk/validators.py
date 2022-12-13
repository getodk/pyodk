from typing import Any, Callable

from pydantic import validators as v
from pydantic.errors import StrError

from pyodk.errors import PyODKError
from pyodk.utils import coalesce


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
    except StrError as err:
        msg = f"{key}: {str(err)}"
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
