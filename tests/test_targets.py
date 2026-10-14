import unittest

from watchtower.core.targets import extract_hostname, normalize_url


class ExtractHostnameTests(unittest.TestCase):
    def test_strips_scheme_and_path(self):
        self.assertEqual(extract_hostname("https://karafa.net"), "karafa.net")
        self.assertEqual(extract_hostname("https://karafa.net/admin?q=1"), "karafa.net")

    def test_strips_port_and_userinfo(self):
        self.assertEqual(extract_hostname("https://user:pass@karafa.net:8443/x"), "karafa.net")
        self.assertEqual(extract_hostname("karafa.net:8080"), "karafa.net")

    def test_bare_domain_unchanged(self):
        self.assertEqual(extract_hostname("karafa.net"), "karafa.net")

    def test_ip_address(self):
        self.assertEqual(extract_hostname("http://192.168.0.1:80"), "192.168.0.1")
        self.assertEqual(extract_hostname("192.168.0.1"), "192.168.0.1")

    def test_empty(self):
        self.assertEqual(extract_hostname(""), "")


class NormalizeUrlTests(unittest.TestCase):
    def test_prepends_scheme_to_bare_host(self):
        self.assertEqual(normalize_url("karafa.net"), "https://karafa.net")

    def test_preserves_existing_scheme(self):
        self.assertEqual(normalize_url("http://karafa.net"), "http://karafa.net")
        self.assertEqual(normalize_url("https://karafa.net/x"), "https://karafa.net/x")

    def test_custom_default_scheme(self):
        self.assertEqual(normalize_url("karafa.net", default_scheme="http"), "http://karafa.net")

    def test_empty(self):
        self.assertEqual(normalize_url(""), "")


if __name__ == "__main__":
    unittest.main()
