"""Build GitHub release notes for a version from CHANGELOG.md.

usage: python scripts/release_notes.py <version> [<previous-tag> <owner/repo>]

Prints the notes to stdout. Exits non-zero if CHANGELOG.md has no section for
the version, so a release cannot go out without notes.
"""
import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"


def extract_section(text, version):
    """Body of the '## <version>' section of a changelog, without its heading."""
    pattern = re.compile(
        rf"^## {re.escape(version)}[ \t]*$(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"CHANGELOG.md has no '## {version}' section")
    body = match.group(1).strip()
    if not body:
        raise ValueError(f"The '## {version}' section of CHANGELOG.md is empty")
    return body


def build_notes(text, version, previous=None, repo=None):
    notes = "## What's Changed\n\n" + extract_section(text, version) + "\n"
    if previous and repo:
        notes += f"\n**Full Changelog**: https://github.com/{repo}/compare/{previous}...{version}\n"
    return notes


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    version = argv[1]
    previous = argv[2] if len(argv) > 2 and argv[2] else None
    repo = argv[3] if len(argv) > 3 and argv[3] else None
    try:
        sys.stdout.write(build_notes(CHANGELOG.read_text(encoding="utf-8"), version, previous, repo))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
