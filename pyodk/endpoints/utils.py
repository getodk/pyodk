import logging
from typing import Any

from requests import Response

from pyodk.errors import PyODKError


def error_if_not_200(response: Response, log: logging.Logger, action: str) -> Any:
    """
    Return the response.json(), or raise an error if the status_code is not 200 (OK).

    :param response: The requests object for the response from ODK Central.
    :param log: The logger to send the error information to.
    :param action: A name for the request action, e.g. "read projects".
    """
    if response.status_code == 200:
        return response.json()
    else:
        msg = (
            f"The {action} request failed."
            f" Status: {response.status_code}, content: {response.content}"
        )
        err = PyODKError(msg)
        log.error(err, exc_info=True)
        raise err
