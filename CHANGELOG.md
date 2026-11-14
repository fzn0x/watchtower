# Changelog

All notable changes to Watchtower are documented here.

## 1.0.7

### Added
- Five recon tools: `katana` (crawler that also parses JavaScript), `gau` (archived URLs for the host), `naabu` (port discovery without root), `dnsx` (DNS records with answers), and `trufflehog` (verified secrets in repositories), for 28 tools in total. `katana` and `gau` also feed the IDOR review. (#9, #48)
- A documentation site at https://fzn0x.github.io/watchtower/, deployed from `main`. (#8, #47)
- Continuous integration: every push and pull request runs the tests on Python 3.10 to 3.13; changes to the Dockerfile, installer, or requirements build the Docker image on Linux and verify Watchtower, the httpx scanner, and every tool inside it. (#42, #45)
- Releases are published by CI from version tags, with notes taken from this changelog. (#42, #45)

### Fixed
- `install_tools.sh`: testssl clones from its new home (the old repository is now empty), gitleaks installs from its declared module path, kiterunner matches versioned release assets and is verified against the release checksums, Go build failures are reported instead of hidden, and Go tools with versioned module paths (`gitleaks`, `amass`, `gobuster`, `ffuf`, `dalfox`) are linked into `/usr/local/bin` on non-Docker installs. (#45)
- A run with no LLM provider configured stops with a clear message before any tool runs, instead of an opaque planner error. (#43, #46)

### Changed
- The Docker image caches its tool layer, so code changes no longer reinstall every tool. (#45)
- The README is now a landing page; long-form documentation moved to the docs site, and Python 3.10 is the documented minimum. (#47)

## 1.0.6

### Fixed
- `--effort` is lowered to the highest level each provider accepts, with a one-time notice. `--effort xhigh` or `max` with Gemini no longer crashes the run. (#30, #38)
- `--flagship` uses the current Opus (`claude-opus-5-5`, or `anthropic/claude-opus-5.5` on OpenRouter), and reasoning runs default to 16000 output tokens instead of 128000. (#31, #38)
- Logic analysis no longer duplicates earlier findings in the state, the database, and the PDF report. (#32, #39)
- The analyst reviews every tool from a parallel step, not only the last one, and logic analysis runs when any tool in the step is a recon trigger. (#33, #39)
- The planner is told the target and whether it is an IP or a hostname, and a model setup error ends the run cleanly instead of crashing. (#34, #39)
- The `httpx` tool runs ProjectDiscovery's scanner with its documented flags instead of Python's httpx client, and `install_tools.sh` installs it again (also as `pd-httpx`), restoring it in the Docker image. (#35, #40)
- Headless mode (`--skip-ask-tools`) offers only installed tools. (#36, #40)

### Added
- `WATCHTOWER_HTTPX_BIN` to point Watchtower at a specific httpx scanner binary.

## 1.0.5

### Added
- Flagship model support with reasoning-aware configuration. New `--flagship`, `--effort`, and `--max-tokens` flags (and `WATCHTOWER_FLAGSHIP` / `WATCHTOWER_EFFORT` / `WATCHTOWER_MAX_TOKENS`) select the provider's top model and set reasoning effort. (#26, #28)

### Changed
- The LLM setup no longer forces `temperature=0` on reasoning models; temperature is omitted when reasoning is enabled so flagship models work. Reasoning is wired per provider (`reasoning_effort` for the OpenAI, Anthropic, and Gemini classes; `extra_body.reasoning` for OpenRouter and custom OpenAI-compatible endpoints).
- Bumped provider pins for `reasoning_effort` support: `langchain-openai>=1.4.1`, `langchain-anthropic>=1.5.3`, `langchain-google-genai>=4.3.1`.

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
