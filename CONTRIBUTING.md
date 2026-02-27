# Contributing to AI Agentic Pentesting Framework

We welcome contributions to this project!

## Development Setup

1. Fork and clone the repository.
2. Install the required dependencies: `pip install -r requirements.txt`
3. We use `make` to manage tasks. See the `Makefile` for available commands.

## Adding a New Tool

1. Create a new module in `watchtower/tools/`.
2. Implement a Python wrapper for the tool that returns the raw output and structured data.
3. Expose the tool to the `Worker` node in `watchtower/agents/worker.py`.

## Adding a New Specialized Agent

1. Create a new module in `watchtower/agents/`.
2. Define the agent's prompts and expected output (using Pydantic/JSON).
3. Connect the agent into the LangGraph state machine in `watchtower/core/agent_manager.py`.

Please ensure that you do not remove any guardrails preventing out-of-scope testing.
