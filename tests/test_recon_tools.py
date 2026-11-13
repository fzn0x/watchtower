import importlib
import sys
import unittest
from unittest import mock

from watchtower.core.targets import is_ip_address, looks_like_git_repo
from watchtower.tools import runner


def run_tool(name, target):
    """Run a wrapper with run_cli_tool replaced, returning (output, calls)."""
    module = importlib.import_module(f"watchtower.tools.{name}")
    calls = []

    def fake(command, **kwargs):
        calls.append((list(command), kwargs))
        return "ok"

    with mock.patch.object(module, "run_cli_tool", side_effect=fake):
        out = module.run(target, auth_metadata={})
    return out, calls


class WrapperCommandTests(unittest.TestCase):
    def test_katana_crawls_the_url(self):
        _, calls = run_tool("katana", "example.com")
        self.assertEqual(calls[0][0], [
            "katana", "-u", "https://example.com", "-silent", "-nc",
            "-d", "2", "-jc", "-timeout", "10", "-rl", "50",
        ])

    def test_naabu_scans_the_host(self):
        _, calls = run_tool("naabu", "https://example.com:8443/app")
        self.assertEqual(calls[0][0], ["naabu", "-host", "example.com", "-top-ports", "1000", "-silent", "-nc"])

    def test_dnsx_reads_the_host_from_stdin(self):
        _, calls = run_tool("dnsx", "https://example.com/x")
        command, kwargs = calls[0]
        self.assertEqual(command, ["dnsx", "-silent", "-nc", "-a", "-aaaa", "-cname", "-mx", "-ns", "-txt", "-resp"])
        self.assertEqual(kwargs["input_text"], "example.com\n")

    def test_dnsx_skips_ip_targets(self):
        out, calls = run_tool("dnsx", "http://127.0.0.1:8088")
        self.assertEqual(calls, [])
        self.assertIn("skipped", out)

    def test_gau_uses_the_host_and_stays_in_scope(self):
        _, calls = run_tool("gau", "https://example.com/path?q=1")
        command = calls[0][0]
        self.assertEqual(command[:2], ["gau", "example.com"])
        self.assertNotIn("--subs", command)
        self.assertIn("--blacklist", command)

    def test_gau_skips_ip_targets(self):
        out, calls = run_tool("gau", "10.0.0.5")
        self.assertEqual(calls, [])
        self.assertIn("skipped", out)

    def test_trufflehog_scans_a_repository(self):
        _, calls = run_tool("trufflehog", "https://github.com/owner/repo")
        self.assertEqual(calls[0][0], [
            "trufflehog", "git", "https://github.com/owner/repo",
            "--results=verified,unknown", "--json", "--no-update",
        ])

    def test_trufflehog_skips_non_repository_targets(self):
        out, calls = run_tool("trufflehog", "https://example.com")
        self.assertEqual(calls, [])
        self.assertIn("skipped", out)


class RunnerStdinTests(unittest.TestCase):
    def test_input_text_reaches_the_tool(self):
        out = runner.run_cli_tool(
            [sys.executable, "-c", "import sys; print(sys.stdin.read().strip().upper())"],
            input_text="abc\n",
        )
        self.assertTrue(out.startswith("ABC"), out)


class TargetHelperTests(unittest.TestCase):
    def test_is_ip_address(self):
        for value in ("127.0.0.1", "10.0.0.5", "::1"):
            self.assertTrue(is_ip_address(value))
        for value in ("example.com", "", "localhost"):
            self.assertFalse(is_ip_address(value))

    def test_git_repo_detection_moved_to_targets(self):
        self.assertTrue(looks_like_git_repo("https://github.com/owner/repo"))
        self.assertFalse(looks_like_git_repo("https://example.com"))


if __name__ == "__main__":
    unittest.main()
