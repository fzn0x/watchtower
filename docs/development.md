# Development

## Setup

```bash
git clone https://github.com/fzn0x/watchtower.git
cd watchtower
pip install -r requirements.txt
python -m unittest discover -s tests
```

The `Makefile` wraps common tasks (`make install`, `make test`, `make run TARGET=...`).

## Adding a tool

1. Create `watchtower/tools/<tool>.py` with a `run(target, **kwargs)` function. Use `extract_hostname` for host or DNS tools and `normalize_url` for web tools, and pass `auth_metadata` to `run_cli_tool`.
2. Add the tool name to `ALL_TOOLS` in `watchtower/tools/__init__.py`. The worker imports wrappers by name, so it needs no changes.
3. If the tool's command name differs from the tool name, add it to `BINARY_ALIASES` in `watchtower/core/binaries.py` so detection works (for example `kiterunner` runs as `kr`).
4. Add its install step to `install_tools.sh` and its command to the `TOOLS=(...)` verification list there. A test fails if a tool is missing from that list.
5. Document it on the [Tools](tools.md) page.

## Adding an agent

1. Create a module in `watchtower/agents/`.
2. Define the agent's prompt and expected output with a Pydantic model.
3. Connect it to the LangGraph state machine in `watchtower/core/agent_manager.py`.

## Continuous integration

Every push to `main` and every pull request runs:

- the test suite on Python 3.10, 3.11, 3.12, and 3.13 with the full requirements installed;
- repository checks (the installer is valid bash, and no em-dashes in tracked text).

Changes to the Dockerfile, installer, or requirements also build the Docker image on Linux and verify it: Watchtower starts, the httpx scanner resolves ahead of Python's httpx client and probes a local server, and every supported tool is installed. Changes to the docs build this site in strict mode.

## Releases

Releases are published by CI. After the release pull request (version bump plus changelog) is merged, pushing the version tag (for example `1.0.7`) on the merged commit runs the release workflow: it checks the tag matches `__version__`, runs the tests and the image check, and publishes the GitHub release with notes from that version's section of `CHANGELOG.md`.

## Contributing and security

See [CONTRIBUTING.md](https://github.com/fzn0x/watchtower/blob/main/CONTRIBUTING.md) and the [security policy](https://github.com/fzn0x/watchtower/blob/main/SECURITY.md). Report vulnerabilities privately through GitHub's private vulnerability reporting, not in public issues or pull requests.
