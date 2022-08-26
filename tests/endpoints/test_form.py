from unittest import TestCase
from unittest.mock import MagicMock, patch

from requests import Session

from pyodk.client import Client
from pyodk.endpoints.form import FormEntity
from tests.resources import CONFIG_DATA, form_data


@patch("pyodk.client.Client._login", MagicMock())
@patch("pyodk.config.read_config", MagicMock(return_value=CONFIG_DATA))
class TestForm(TestCase):
    def test_read_all__ok(self):
        """Should return a list of FormEntity objects."""
        fixture = form_data.test_forms
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture
            with Client() as client:
                observed = client.form.read_all()
        self.assertEqual(4, len(observed))
        for i, o in enumerate(observed):
            with self.subTest(i):
                self.assertIsInstance(o, FormEntity)

    def test_read__ok(self):
        """Should return a FormEntity object."""
        fixture = form_data.test_forms[0]
        with patch.object(Session, "get") as mock_session:
            mock_session.return_value.status_code = 200
            mock_session.return_value.json.return_value = fixture
            with Client() as client:
                # Specify project
                observed = client.form.read(
                    project_id=fixture["projectId"], form_id=fixture["xmlFormId"]
                )
                self.assertIsInstance(observed, FormEntity)
                # Use default
                observed = client.form.read(form_id=fixture["xmlFormId"])
                self.assertIsInstance(observed, FormEntity)
