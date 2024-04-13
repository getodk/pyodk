from pathlib import Path
from unittest import TestCase

from pyodk._utils.session import Session


class TestSession(TestCase):
    def test_base_url_validate(self):
        """Should return base_url suffixed with '/{version}/', if not already added."""
        cases = (
            ("https://example.com", "https://example.com/v1/"),
            ("https://example.com/", "https://example.com/v1/"),
            ("https://example.com/v1", "https://example.com/v1/"),
            ("https://example.com/v1/", "https://example.com/v1/"),
            ("https://example.com/subpath/v1", "https://example.com/subpath/v1/"),
            ("https://example.com/subpath/v1/", "https://example.com/subpath/v1/"),
        )
        for base_url, expected in cases:
            with self.subTest(msg=f"{base_url}"):
                observed = Session.base_url_validate(base_url=base_url, api_version="v1")
                self.assertEqual(expected, observed)

    def test_urlformat(self):
        """Should replace input fields with url-encoded values."""
        url = "projects/{project_id}/forms/{form_id}"
        test_cases = (
            # Basic latin string
            ({"project_id": 1, "form_id": "a"}, "projects/1/forms/a"),
            # integer
            ({"project_id": 1, "form_id": 1}, "projects/1/forms/1"),
            # latin symbols
            ({"project_id": 1, "form_id": "+-_*%*"}, "projects/1/forms/%2B-_*%25*"),
            # lower case e, with combining acute accent (2 symbols)
            ({"project_id": 1, "form_id": "tést"}, "projects/1/forms/te%CC%81st"),
            # lower case e with acute (1 symbol)
            ({"project_id": 1, "form_id": "tést"}, "projects/1/forms/t%C3%A9st"),
            # white heavy check mark
            ({"project_id": 1, "form_id": "✅"}, "projects/1/forms/%E2%9C%85"),
        )
        for params, expected in test_cases:
            with self.subTest(msg=str(params)):
                self.assertEqual(expected, Session.urlformat(url, **params))

    def test_urlquote(self):
        """Should url-encode input values."""
        test_cases = (
            # Basic latin string
            ("test.xlsx", "test"),
            # integer
            ("1.xls", "1"),
            # latin symbols
            ("+-_*%*.xls", "%2B-_*%25*"),
            # spaces
            ("my form.xlsx", "my%20form"),
            # lower case e, with combining acute accent (2 symbols)
            ("tést.xlsx", "te%CC%81st"),
            # lower case e with acute (1 symbol)
            ("tést", "t%C3%A9st"),
            # white heavy check mark
            ("✅.xlsx", "%E2%9C%85"),
        )
        for params, expected in test_cases:
            with self.subTest(msg=str(params)):
                self.assertEqual(expected, Session.urlquote(Path(params).stem))
