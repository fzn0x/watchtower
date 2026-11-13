# Troubleshooting

## No LLM provider is configured

Watchtower stops before running any tool when no provider is set. Add one of `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY` to `.env`, or pass `--provider`, `--model`, and `--apikey`. See [LLM providers](providers.md).

## `model: [model_name] does not support feature: structured-outputs`

This happens with experimental, free, or unsupported models on OpenRouter (for example some Qwen or DeepSeek variants). Watchtower asks the model for well-formed JSON. Switch `OPENROUTER_MODEL_NAME` in `.env` to a current, fully supported commercial model, such as:

- `anthropic/claude-sonnet-5.5`
- `openai/gpt-5.6`
- `google/gemini-3.8-flash`

Watchtower parses JSON from plain text for models without native structured output, but commercial models give much better pentesting logic.

## `429 Too Many Requests: [model]:free is temporarily rate-limited upstream`

You are using a `:free` model on OpenRouter and the upstream providers are rate-limiting free traffic. Wait it out or switch to a different (or paid) model.

## Reasoning effort was lowered

A notice such as `Reasoning effort 'max' is not supported by the gemini provider; using 'high' instead` means the provider does not accept the level you asked for. Watchtower used the highest level it does accept.

## Content discovery wordlist (`ffuf`, `gobuster`)

These tools need a wordlist. Watchtower uses `WATCHTOWER_WORDLIST` if set, then common SecLists/dirb locations, and finally a small list bundled with Watchtower. To use your own:

```bash
export WATCHTOWER_WORDLIST=/usr/share/seclists/Discovery/Web-Content/common.txt
```

## `httpx` reports "could not run" or is shown as missing

Watchtower's `httpx` tool is ProjectDiscovery's HTTP prober. Python's `httpx` package, installed with Watchtower's requirements, ships a different `httpx` command that can come first on your `PATH` (for example inside a virtualenv). Watchtower skips that command and looks for the scanner as `pd-httpx`, `httpx-toolkit`, in Go's `bin` directory, then on `PATH`. `install_tools.sh` installs it and adds `pd-httpx`. To point at a specific binary:

```bash
export WATCHTOWER_HTTPX_BIN=/root/go/bin/httpx
```

## A tool is listed as missing

Run `install_tools.sh`, or install the tool yourself and make sure it is on your `PATH`. A few tools are detected under another command name: `kiterunner` as `kr`, and `testssl` as `testssl.sh`.
