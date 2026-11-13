import os
from pathlib import Path

# Common install locations for a directory/content-discovery wordlist.
# Checked in order when no explicit wordlist is configured.
_COMMON_CANDIDATES = [
    "/usr/share/seclists/Discovery/Web-Content/common.txt",
    "/usr/share/wordlists/seclists/Discovery/Web-Content/common.txt",
    "/usr/share/wordlists/dirb/common.txt",
    "/usr/share/dirb/wordlists/common.txt",
    "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
]

# Small bundled fallback shipped with the package so ffuf/gobuster always have
# a valid wordlist even on a machine with none of the above installed.
_BUNDLED = Path(__file__).resolve().parent.parent / "data" / "common.txt"


def default_wordlist() -> str:
    """Resolve a wordlist path for content-discovery tools.

    Resolution order:
      1. ``WATCHTOWER_WORDLIST`` environment variable, if it points to a file.
      2. A known SecLists/dirb location present on the system.
      3. The small wordlist bundled with Watchtower.
    """
    env = os.getenv("WATCHTOWER_WORDLIST")
    if env and Path(env).is_file():
        return env

    for candidate in _COMMON_CANDIDATES:
        if Path(candidate).is_file():
            return candidate

    return str(_BUNDLED)
