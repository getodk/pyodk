from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from requests import Session

from pyodk import config
from pyodk.client import Client
from pyodk.endpoints.auth import AuthService
from pyodk.errors import PyODKError
from tests.resources import CONFIG_DATA


@patch("pyodk.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestAuth(TestCase):
    """Test login."""

    def test_get_new_token__ok(self):
        """Should return the token from the response data."""
        with patch.object(Session, "post") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = {"token": "here"}
            conf = config.read_config().central
            client = Client()
            with client.session:
                token = client.auth.get_new_token(conf.username, conf.password)
        self.assertEqual("here", token)

    def test_get_new_token__error__response_status(self):
        """Should raise an error if login request is not OK (HTTP 200)."""
        with patch.object(Session, "post") as mock_session:
            mock_session.return_value.status_code = 404
            conf = config.read_config().central
            client = Client()
            with client.session, self.assertRaises(PyODKError) as err:
                client.auth.get_new_token(conf.username, conf.password)
        msg = "The login request failed. Status:"
        self.assertTrue(err.exception.args[0].startswith(msg))

    def test_get_new_token__error__response_data(self):
        """Should raise an error if login token not found in response data."""
        with patch.object(Session, "post") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = {"not": "here"}
            conf = config.read_config().central
            client = Client()
            with client.session, self.assertRaises(PyODKError) as err:
                client.auth.get_new_token(conf.username, conf.password)
        msg = "The login request was OK but there was no token in the response."
        self.assertTrue(err.exception.args[0].startswith(msg))

    def test_verify_token__ok(self):
        """Should return the token."""
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            client = Client()
            with client.session:
                token = client.auth.verify_token(token="123")
        self.assertEqual("123", token)

    def test_verify_token__error__response_status(self):
        """Should raise an error if the request is not OK (HTTP 200)."""
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 401
            client = Client()
            with client.session, self.assertRaises(PyODKError) as err:
                client.auth.verify_token(token="123")
        msg = "The token verification request failed. Status:"
        self.assertTrue(err.exception.args[0].startswith(msg))


class TestAuthWithCleanCache(TestCase):
    """Tests without the cache file to start with. Delete afterwards."""

    def setUp(self) -> None:
        config.delete_cache()
        self.assertFalse(Path.exists(config.get_cache_path()))
        self.client = Client()

    def tearDown(self) -> None:
        config.delete_cache()

    def test_get_token__new__ok(self):
        """Should return the token, and write it to the cache file."""
        with patch.multiple(
            AuthService,
            get_new_token=MagicMock(return_value="123"),
        ):
            token = self.client.auth.get_token(username="user", password="pass")
            self.assertEqual("123", token)
            cache = config.read_cache_token()
            self.assertEqual("123", cache)

    def test_get_token__new__error__response(self):
        """Should raise an error, when no existing token and new token request fails."""
        verify_mock = MagicMock()
        verify_mock.side_effect = PyODKError("The token verification request failed.")
        get_new_mock = MagicMock()
        get_new_mock.side_effect = PyODKError("The login request failed.")
        with patch.multiple(
            AuthService,
            verify_token=verify_mock,
            get_new_token=get_new_mock,
        ), self.assertRaises(PyODKError) as err:
            self.client.auth.get_token(username="user", password="pass")
        self.assertTrue(err.exception.args[0].startswith("The login request failed."))
        self.assertFalse(Path.exists(config.get_cache_path()))

    def test_get_token__existing__ok(self):
        """Should return the token from the cache file."""
        with patch.multiple(
            AuthService,
            verify_token=MagicMock(return_value="123"),
        ):
            config.write_cache("token", "123")
            token = self.client.auth.get_token(username="user", password="pass")
            self.assertEqual("123", token)
            cache = config.read_cache_token()
            self.assertEqual("123", cache)

    def test_get_token__existing__error__response(self):
        """Should get a new token, when verification of an existing token fails."""
        verify_mock = MagicMock()
        verify_mock.side_effect = PyODKError("The token verification request failed.")
        with patch.multiple(
            AuthService,
            verify_token=verify_mock,
            get_new_token=MagicMock(return_value="123"),
        ):
            config.write_cache("token", "123")
            token = self.client.auth.get_token(username="user", password="pass")
            self.assertEqual("123", token)
            cache = config.read_cache_token()
            self.assertEqual("123", cache)
            self.assertEqual(1, verify_mock.call_count)
