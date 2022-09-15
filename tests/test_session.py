from unittest import TestCase

from pyodk.session import Session


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
