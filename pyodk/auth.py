from typing import Optional

from pyodk import config
from pyodk.errors import PyODKError


class AuthService:
    def __init__(self, session):
        self.session = session

    def verify_token(self, token: str) -> str:
        """
        Check with Central that a token is valid.

        :param token: The token to check.
        :return:
        """
        response = self.session.s.get(
            url=f"{self.session.base_url}/v1/users/current",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        if response.status_code == 200:
            return token
        else:
            raise PyODKError("The login token was not valid.")

    def get_new_token(self, username: str, password: str) -> str:
        """
        Get a new token from Central by creating a new session.

        https://odkcentral.docs.apiary.io/#reference/authentication/session-authentication/logging-in

        :param username: The username of the Web User to auth with.
        :param password: The Web User's password.
        :return: The session token.
        """
        response = self.session.s.post(
            url=f"{self.session.base_url}/v1/sessions",
            json={"email": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 200:
            data = response.json()
            if "token" not in data:
                msg = "The login request was OK but there was no token in the response."
                raise PyODKError(msg)
            else:
                return data["token"]
        else:
            msg = (
                f"The login request failed."
                f" Status: {response.status_code}, content: {response.content}"
            )
            raise PyODKError(msg)

    def get_token(
        self, username: str, password: str, cache_file: Optional[str] = None
    ) -> str:
        """
        Get a verified session token with the provided credential.

        Tries to verify token in cache_file, or requests a new session.

        :param username: The username of the Web User to auth with.
        :param password: The Web User's password.
        :param cache_file: The file path for caching the session token. This is
          recommended to minimize the login events logged on the server.
        :return: The session token or None if anything has gone wrong
        """
        token = None
        if cache_file is not None:
            try:
                token = config.read_cache_token()
                self.verify_token(token=token)
            except PyODKError:
                pass

        if token is None:
            token = self.get_new_token(username=username, password=password)

        if cache_file is not None:
            config.write_cache(key="token", value=token)

        return token
