# Contributing to Watchtower

We welcome contributions to this project!

## Development Setup

1. Fork and clone the repository.
2. Install the required dependencies: `pip install -r requirements.txt`
3. We use `make` to manage tasks. See the `Makefile` for available commands.

## Adding a New Tool

1. Create a module `watchtower/tools/<tool>.py` with a `run(target, **kwargs)` function. Use `extract_hostname` for host/DNS tools and `normalize_url` for web tools, and propagate `auth_metadata` to the `run_cli_tool` helper.
2. Add the tool name to the `all_tools` list in `watchtower/main.py`. The `Worker` node imports tool modules by name, so it needs no changes.
3. If the tool's binary name on `PATH` differs from the tool name, add it to `binary_aliases` in `watchtower/main.py` so detection works (see `kiterunner`/`kr`).
4. Add the install steps to `install_tools.sh` so the bundled installer and the Docker image pick it up.
5. List the tool in the README Features section.

## Adding a New Specialized Agent

1. Create a new module in `watchtower/agents/`.
2. Define the agent's prompts and expected output (using Pydantic/JSON).
3. Connect the agent into the LangGraph state machine in `watchtower/core/agent_manager.py`.

You are responsible for ensuring you only test targets you are explicitly authorized to test. Watchtower does not enforce target scope, so take care not to point it at systems you do not own or have permission to assess.
