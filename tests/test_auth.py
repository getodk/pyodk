from unittest import TestCase
from unittest.mock import patch

from requests import Session

from pyodk import config
from pyodk.client import Client
from pyodk.errors import PyODKError


class TestAuth(TestCase):
    """Test login."""

    def test_get_new_token__good_response(self):
        """Should return the token from the response data."""
        with patch.object(Session, "post") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json = lambda: {"token": "here"}
            conf = config.read_config()
            client = Client(base_url=conf["url"])
            with client.session:
                token = client.auth.get_new_token(conf["username"], conf["password"])
        self.assertEqual("here", token)

    def test_get_new_token__bad_response_status(self):
        """Should raise an error if login request is not OK (HTTP 200)."""
        with patch.object(Session, "post") as mock_session:
            mock_session.return_value.status_code = 404
            conf = config.read_config()
            client = Client(base_url=conf["url"])
            with client.session:
                with self.assertRaises(PyODKError) as err:
                    client.auth.get_new_token(conf["username"], conf["password"])
        msg = "The login request failed. Status:"
        self.assertTrue(err.exception.args[0].startswith(msg))

    def test_get_new_token__bad_response_data(self):
        """Should raise an error if login token not found in response data."""
        with patch.object(Session, "post") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json = lambda: {"not": "here"}
            conf = config.read_config()
            client = Client(base_url=conf["url"])
            with client.session:
                with self.assertRaises(PyODKError) as err:
                    client.auth.get_new_token(conf["username"], conf["password"])
        msg = "The login request was OK but there was no token in the response."
        self.assertTrue(err.exception.args[0].startswith(msg))
