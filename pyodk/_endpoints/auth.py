import logging
from typing import TYPE_CHECKING

from pyodk._utils import config
from pyodk.errors import PyODKError

if TYPE_CHECKING:
    from pyodk._utils.session import Session

log = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: "Session", cache_path: str | None = None) -> None:
        self.session: "Session" = session
        self.cache_path: str = cache_path

    def verify_token(self, token: str) -> str:
        """
        Check with Central that a token is valid.

        :param token: The token to check.
        :return:
        """
        response = self.session.get(
            url="users/current",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        if response.status_code == 200:
            return token
        else:
            msg = (
                f"The token verification request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            err = PyODKError(msg)
            log.error(err, exc_info=True)
            raise err

    def get_new_token(self, username: str, password: str) -> str:
        """
        Get a new token from Central by creating a new session.

        https://docs.getodk.org/central-api-authentication/#logging-in

        :param username: The username of the Web User to auth with.
        :param password: The Web User's password.
        :return: The session token.
        """
        response = self.session.post(
            url="sessions",
            json={"email": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 200:
            data = response.json()
            if "token" not in data:
                msg = "The login request was OK but there was no token in the response."
                err = PyODKError(msg)
                log.error(err, exc_info=True)
                raise err
            else:
                return data["token"]
        else:
            msg = (
                f"The login request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            err = PyODKError(msg, response)
            log.error(err, exc_info=True)
            raise err

    def get_token(self, username: str, password: str) -> str:
        """
        Get a verified session token with the provided credential.

        Tries to verify token in cache_file, or requests a new session.

        :param username: The username of the Web User to auth with.
        :param password: The Web User's password.
        :return: The session token or None if anything has gone wrong
        """
        try:
            token = config.read_cache_token(cache_path=self.cache_path)
            return self.verify_token(token=token)
        except PyODKError:
            # Couldn't read the token, or it wasn't valid.
            pass

        token = self.get_new_token(username=username, password=password)
        config.write_cache(key="token", value=token, cache_path=self.cache_path)
        return token
