# Getting started

## Prerequisites

- **OS**: Linux or macOS recommended. Windows works through WSL2 for most networking tools.
- **Python**: 3.10 or newer.
- **An LLM provider**: an API key for OpenRouter, OpenAI, or Gemini, or a custom provider (see [LLM providers](providers.md)).
- **The security tools themselves** (`nmap`, `nuclei`, `httpx`, ...) installed on your `PATH`. Watchtower detects which ones are missing and leaves them out.

## Install the security tools

The bundled installer sets up every supported tool on Debian/Ubuntu, Fedora/RHEL, and Arch (run it as root):

```bash
sudo ./install_tools.sh
```

It installs system packages, Go (Go-based tools switch to a newer Go toolchain automatically when they need one), and the Go, Ruby, Python, npm, and git-based tools, then prints which tools it could find.

## Install Watchtower

```bash
git clone https://github.com/fzn0x/watchtower.git
cd watchtower

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configure a provider

```bash
cp .env.example .env
```

Set **one** of these keys in `.env`:

```ini
OPENAI_API_KEY=""
GEMINI_API_KEY=""
OPENROUTER_API_KEY=""
```

Optionally choose the model for each provider. The defaults are balanced, current models:

```ini
OPENAI_MODEL_NAME="gpt-5.6"
GEMINI_MODEL_NAME="gemini-3.8-flash"
OPENROUTER_MODEL_NAME="anthropic/claude-sonnet-5.5"
```

!!! note
    Model names change often. Set these to a current model your provider offers.

If no provider is configured, Watchtower stops before running any tool and tells you which keys or flags to set.

## Run with Docker

The image installs every tool through the same installer:

```bash
docker build -t watchtower .
docker run --rm --env-file .env watchtower python -m watchtower.main -t https://example.com --skip-ask-tools
```

Or with Docker Compose, which mounts the project directory and reads `.env`:

```bash
docker compose run --rm agentic-pentest python -m watchtower.main -t https://example.com --skip-ask-tools
```
