# Changelog

All notable changes to Watchtower are documented here.

## 1.0.4

### Fixed
- Analyst node no longer crashes on its error path (it logged without importing `logging`). (#10)
- Tool detection recognizes tools installed under a different binary name, so kiterunner (`kr`) is no longer reported missing. (#11)
- kiterunner wrapper forwards auth cookies and headers like the other tools. (#12)
- `ffuf` and `gobuster` resolve a real wordlist (`WATCHTOWER_WORDLIST`, common system locations, or a small bundled list) instead of a path that never existed. (#13)
- `gitleaks` scans a cloned target repository instead of the current working directory, and skips clearly for non-repository targets. (#14)
- Reports and memory are scoped per run, so a report covers a single assessment instead of every finding ever stored. (#15)

### Changed
- Reconnaissance runs tools concurrently with a capped thread pool, matching the documented parallel behavior. (#18)
- Removed unused dependencies: `chromadb`, `SQLAlchemy`, `markdown`, `langchain-ollama`. (#16)

### Added
- `--version` flag and a single `__version__` source. (#17)
- `--run` option to choose which run `--report` renders (defaults to the latest).

## 1.0.3
See the release notes: https://github.com/fzn0x/watchtower/releases/tag/1.0.3

## 1.0.2
See the release notes: https://github.com/fzn0x/watchtower/releases/tag/1.0.2

## 1.0.1
See the release notes: https://github.com/fzn0x/watchtower/releases/tag/1.0.1

## 1.0.0
Initial release.
