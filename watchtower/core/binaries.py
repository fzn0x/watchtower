"""Locate tool binaries, including tools installed under other names.

Python's `httpx` package (pulled in by the LLM SDKs) installs its own `httpx`
command, which can shadow ProjectDiscovery's `httpx` scanner on PATH. The
helpers here tell the two apart so Watchtower runs the scanner.
"""

import os
import shutil
import sysconfig
from pathlib import Path

# Tools invoked under a different binary name than their key.
BINARY_ALIASES = {
    "testssl": ["testssl.sh"],
    "kiterunner": ["kr"],
}

# Other names ProjectDiscovery httpx is installed under (install_tools.sh adds
# pd-httpx; Kali packages it as httpx-toolkit).
_PD_HTTPX_NAMES = ["pd-httpx", "httpx-toolkit"]


def _norm(path) -> str:
    return os.path.normcase(os.path.realpath(path))


def _python_scripts_dirs() -> set:
    """Directories where Python installs console scripts for this interpreter."""
    dirs = set()
    for scheme in (None, f"{os.name}_user"):
        try:
            path = sysconfig.get_path("scripts", scheme) if scheme else sysconfig.get_path("scripts")
        except KeyError:
            continue
        if path:
            dirs.add(_norm(path))
    return dirs


_ENTRY_POINT_MARKER = b"from httpx import main"


def is_python_httpx_cli(path) -> bool:
    """True if `path` is the console script installed by Python's httpx package."""
    try:
        real = _norm(path)
        size = os.path.getsize(real)
        with open(real, "rb") as fh:
            head = fh.read(4096)
            fh.seek(max(0, size - 65536))
            tail = fh.read()
    except OSError:
        return False
    if head.startswith(b"#!"):
        # POSIX: pip writes a short Python script that imports the entry point.
        # A real scanner binary starts with an ELF/Mach-O header instead.
        return _ENTRY_POINT_MARKER in head
    # Windows: console scripts are .exe launchers with the script appended,
    # uncompressed, at the end of the file. This catches any Python install,
    # not just the running interpreter's.
    if _ENTRY_POINT_MARKER in tail:
        return True
    if os.name == "nt":
        # Fallback: launchers in this interpreter's Scripts directory.
        return os.path.dirname(real) in _python_scripts_dirs()
    return False


def _which_all(name) -> list:
    """Every match for `name` on PATH, in PATH order, without duplicates."""
    found, seen = [], set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        hit = shutil.which(name, path=directory)
        if hit and _norm(hit) not in seen:
            seen.add(_norm(hit))
            found.append(hit)
    return found


def find_pd_httpx():
    """Path to ProjectDiscovery's httpx scanner, or None if only the Python client exists.

    Order: WATCHTOWER_HTTPX_BIN, alternate names (pd-httpx, httpx-toolkit), Go's
    bin directories, then any `httpx` on PATH that is not Python's client CLI.
    """
    override = os.getenv("WATCHTOWER_HTTPX_BIN")
    if override:
        resolved = shutil.which(override) or (override if os.path.isfile(override) else None)
        if resolved:
            return resolved

    for name in _PD_HTTPX_NAMES:
        hit = shutil.which(name)
        if hit:
            return hit

    go_bins = []
    if os.getenv("GOPATH"):
        go_bins.append(os.path.join(os.getenv("GOPATH"), "bin"))
    go_bins.append(os.path.join(str(Path.home()), "go", "bin"))
    for directory in go_bins:
        hit = shutil.which("httpx", path=directory)
        if hit and not is_python_httpx_cli(hit):
            return hit

    for hit in _which_all("httpx"):
        if not is_python_httpx_cli(hit):
            return hit
    return None


def is_tool_installed(tool) -> bool:
    if tool == "httpx":
        return find_pd_httpx() is not None
    candidates = [tool] + BINARY_ALIASES.get(tool, [])
    return any(shutil.which(name) for name in candidates)


def split_installed(tools):
    """Partition tool names into (installed, missing), preserving order."""
    installed = [t for t in tools if is_tool_installed(t)]
    missing = [t for t in tools if t not in installed]
    return installed, missing
