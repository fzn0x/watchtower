import importlib.util
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "release_notes.py"
_spec = importlib.util.spec_from_file_location("release_notes", _SCRIPT)
release_notes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release_notes)

SAMPLE = """# Changelog

## 1.2.0

### Added
- New thing. (#5)

## 1.1.0

### Fixed
- Old fix. (#3)
"""


class ReleaseNotesTests(unittest.TestCase):
    def test_extracts_only_the_requested_section(self):
        body = release_notes.extract_section(SAMPLE, "1.2.0")
        self.assertIn("New thing. (#5)", body)
        self.assertNotIn("Old fix", body)

    def test_last_section_runs_to_end_of_file(self):
        self.assertIn("Old fix. (#3)", release_notes.extract_section(SAMPLE, "1.1.0"))

    def test_missing_version_is_an_error(self):
        with self.assertRaises(ValueError):
            release_notes.extract_section(SAMPLE, "9.9.9")

    def test_version_dots_are_literal(self):
        # "1.2.0" must not match a heading like "1x2y0".
        with self.assertRaises(ValueError):
            release_notes.extract_section("## 1x2y0\n\nstuff\n", "1.2.0")

    def test_notes_include_compare_link(self):
        notes = release_notes.build_notes(SAMPLE, "1.2.0", "1.1.0", "fzn0x/watchtower")
        self.assertTrue(notes.startswith("## What's Changed"))
        self.assertIn("https://github.com/fzn0x/watchtower/compare/1.1.0...1.2.0", notes)

    def test_real_changelog_has_current_version(self):
        # The release workflow refuses to publish without notes for the tag.
        from watchtower import __version__
        text = release_notes.CHANGELOG.read_text(encoding="utf-8")
        self.assertTrue(release_notes.extract_section(text, __version__))


if __name__ == "__main__":
    unittest.main()
