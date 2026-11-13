import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from watchtower.core import binaries

# What pip writes for Python httpx's console script on POSIX.
PY_CLI = (b"#!/usr/bin/python3\n# -*- coding: utf-8 -*-\nimport re\nimport sys\n"
          b"from httpx import main\nif __name__ == '__main__':\n    sys.exit(main())\n")
# Stand-in for a compiled scanner binary.
REAL_BIN = b"\x7fELF\x02\x01\x01 not a script" if os.name != "nt" else b"MZ\x90\x00 not a script"


def _make_exe(directory, name, content):
    path = os.path.join(directory, name + (".exe" if os.name == "nt" else ""))
    with open(path, "wb") as fh:
        fh.write(content)
    if os.name != "nt":
        os.chmod(path, 0o755)
    return path


def _isolated_env(path_dirs, home, **extra):
    env = {k: v for k, v in os.environ.items() if k not in ("WATCHTOWER_HTTPX_BIN", "GOPATH")}
    env["PATH"] = os.pathsep.join(path_dirs)
    env.update(extra)
    return [
        mock.patch.dict(os.environ, env, clear=True),
        mock.patch.object(binaries.Path, "home", return_value=Path(home)),
    ]


class _Tmp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = self._tmp.name
        self.py_dir = os.path.join(root, "pybin")
        self.real_dir = os.path.join(root, "realbin")
        self.home = os.path.join(root, "home")
        for d in (self.py_dir, self.real_dir, self.home):
            os.makedirs(d)

    def tearDown(self):
        self._tmp.cleanup()

    def run_with(self, path_dirs, fn, **extra):
        patches = _isolated_env(path_dirs, self.home, **extra)
        for p in patches:
            p.start()
        try:
            return fn()
        finally:
            for p in reversed(patches):
                p.stop()


class PythonCliDetectionTests(_Tmp):
    def test_detects_python_console_script(self):
        self.assertTrue(binaries.is_python_httpx_cli(_make_exe(self.py_dir, "httpx", PY_CLI)))

    def test_detects_windows_launcher_from_any_python(self):
        # pip's Windows launchers are .exe files with the script appended in an
        # uncompressed zip; the global Python's copy was missed before.
        launcher = (b"MZ\x90\x00" + b"\x00" * 8000 + b"#!C:\\Python310\\python.exe\r\n"
                    b"PK\x03\x04__main__.py" + PY_CLI.split(b"\n", 1)[1])
        self.assertTrue(binaries.is_python_httpx_cli(_make_exe(self.real_dir, "httpx", launcher)))

    def test_real_binary_is_not_flagged(self):
        self.assertFalse(binaries.is_python_httpx_cli(_make_exe(self.real_dir, "httpx", REAL_BIN)))

    def test_missing_file_is_not_flagged(self):
        self.assertFalse(binaries.is_python_httpx_cli(os.path.join(self.py_dir, "nope")))


class FindPdHttpxTests(_Tmp):
    def test_skips_python_cli_and_finds_scanner_later_on_path(self):
        _make_exe(self.py_dir, "httpx", PY_CLI)
        real = _make_exe(self.real_dir, "httpx", REAL_BIN)
        found = self.run_with([self.py_dir, self.real_dir], binaries.find_pd_httpx)
        self.assertEqual(os.path.normcase(found), os.path.normcase(real))

    def test_none_when_only_python_cli_exists(self):
        # Regression: this is what a fresh virtualenv looks like.
        _make_exe(self.py_dir, "httpx", PY_CLI)
        self.assertIsNone(self.run_with([self.py_dir], binaries.find_pd_httpx))

    def test_prefers_pd_httpx_name(self):
        _make_exe(self.py_dir, "httpx", PY_CLI)
        pd = _make_exe(self.real_dir, "pd-httpx", REAL_BIN)
        found = self.run_with([self.py_dir, self.real_dir], binaries.find_pd_httpx)
        self.assertEqual(os.path.normcase(found), os.path.normcase(pd))

    def test_checks_go_bin_in_home(self):
        go_bin = os.path.join(self.home, "go", "bin")
        os.makedirs(go_bin)
        real = _make_exe(go_bin, "httpx", REAL_BIN)
        found = self.run_with([self.py_dir], binaries.find_pd_httpx)
        self.assertEqual(os.path.normcase(found), os.path.normcase(real))

    def test_env_override_wins(self):
        custom = _make_exe(self.real_dir, "my-httpx", REAL_BIN)
        found = self.run_with([], binaries.find_pd_httpx, WATCHTOWER_HTTPX_BIN=custom)
        self.assertEqual(found, custom)


class InstalledToolTests(_Tmp):
    def test_alias_counts_as_installed(self):
        _make_exe(self.real_dir, "kr", REAL_BIN)
        self.assertTrue(self.run_with([self.real_dir], lambda: binaries.is_tool_installed("kiterunner")))

    def test_missing_tool(self):
        self.assertFalse(self.run_with([self.real_dir], lambda: binaries.is_tool_installed("nmap")))

    def test_httpx_needs_the_scanner(self):
        _make_exe(self.py_dir, "httpx", PY_CLI)
        self.assertFalse(self.run_with([self.py_dir], lambda: binaries.is_tool_installed("httpx")))

    def test_split_installed_preserves_order(self):
        _make_exe(self.real_dir, "nmap", REAL_BIN)
        _make_exe(self.real_dir, "ffuf", REAL_BIN)
        installed, missing = self.run_with(
            [self.real_dir], lambda: binaries.split_installed(["nmap", "httpx", "ffuf", "whatweb"])
        )
        self.assertEqual(installed, ["nmap", "ffuf"])
        self.assertEqual(missing, ["httpx", "whatweb"])


if __name__ == "__main__":
    unittest.main()
