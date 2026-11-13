import os
import tempfile
import unittest
from pathlib import Path

from watchtower.core.wordlists import default_wordlist
from watchtower.tools.gitleaks import _looks_like_git_repo


class DefaultWordlistTests(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("WATCHTOWER_WORDLIST", None)

    def tearDown(self):
        if self._saved is not None:
            os.environ["WATCHTOWER_WORDLIST"] = self._saved
        else:
            os.environ.pop("WATCHTOWER_WORDLIST", None)

    def test_env_override_wins_when_file_exists(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
            fh.write("admin\nlogin\n")
            path = fh.name
        try:
            os.environ["WATCHTOWER_WORDLIST"] = path
            self.assertEqual(default_wordlist(), path)
        finally:
            os.unlink(path)

    def test_env_override_ignored_when_missing(self):
        os.environ["WATCHTOWER_WORDLIST"] = "/no/such/wordlist-xyz.txt"
        self.assertNotEqual(default_wordlist(), "/no/such/wordlist-xyz.txt")

    def test_fallback_path_is_a_real_file(self):
        # With no env override, the resolved wordlist must exist on disk
        # (either a system list or the bundled one).
        self.assertTrue(Path(default_wordlist()).is_file())


class GitRepoDetectionTests(unittest.TestCase):
    def test_true_cases(self):
        self.assertTrue(_looks_like_git_repo("https://github.com/owner/repo"))
        self.assertTrue(_looks_like_git_repo("https://gitlab.com/group/proj"))
        self.assertTrue(_looks_like_git_repo("https://example.com/thing.git"))
        self.assertTrue(_looks_like_git_repo("git@placeholder.git"))

    def test_false_cases(self):
        self.assertFalse(_looks_like_git_repo("https://example.com"))
        self.assertFalse(_looks_like_git_repo("example.com"))
        self.assertFalse(_looks_like_git_repo("https://github.com/owner"))
        self.assertFalse(_looks_like_git_repo("192.168.0.1"))
        self.assertFalse(_looks_like_git_repo(""))


if __name__ == "__main__":
    unittest.main()
