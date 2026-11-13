import importlib
import re
import unittest
from pathlib import Path

from watchtower.tools import ALL_TOOLS

INSTALLER = Path(__file__).resolve().parent.parent / "install_tools.sh"

# Tools the installer verifies under a different command name.
INSTALLER_NAMES = {"httpx": "pd-httpx", "kiterunner": "kr"}


class ToolCatalogTests(unittest.TestCase):
    def test_every_tool_has_a_wrapper(self):
        for name in ALL_TOOLS:
            with self.subTest(tool=name):
                module = importlib.import_module(f"watchtower.tools.{name}")
                self.assertTrue(callable(getattr(module, "run", None)))

    def test_installer_installs_every_tool(self):
        # Regression: httpx was supported but never installed by install_tools.sh.
        text = INSTALLER.read_text(encoding="utf-8")
        match = re.search(r"^TOOLS=\((.*?)\)", text, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "install_tools.sh has no TOOLS=(...) summary list")
        verified = set(match.group(1).replace("\\", " ").split())
        for name in ALL_TOOLS:
            with self.subTest(tool=name):
                self.assertIn(INSTALLER_NAMES.get(name, name), verified)

    def test_no_duplicates(self):
        self.assertEqual(len(ALL_TOOLS), len(set(ALL_TOOLS)))


if __name__ == "__main__":
    unittest.main()
