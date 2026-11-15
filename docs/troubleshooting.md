# Troubleshooting

## No LLM provider is configured

Watchtower stops before running any tool when no provider is set. Add one of `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `ANTHROPIC_API_KEY` to `.env`, sign in to Claude with `ant auth login`, pass `--provider`, `--model`, and `--apikey`, or run a local model with `--provider ollama --model <name>`. See [LLM providers](providers.md).

## Claude uses the wrong account, or `Could not resolve authentication method`

Run `ant auth status` to see which credential the Anthropic SDK picked. An `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` set in your shell or `.env` wins over an `ant auth login` profile. If a profile that used to work starts failing, its sign-in has expired: run `ant auth login` again. See [Claude](providers.md#claude).

## A local model gives empty, cut-off, or malformed answers

The model's context window is probably too small for Watchtower's prompts, so the server dropped part of them. Raise the context length (in Ollama, `num_ctx` in a Modelfile) or use a larger model. See [Local models](providers.md#local-models).

## `Connection refused` with a local model

Check that the server is running and that the URL matches: `curl http://localhost:11434/v1/models` for Ollama. From inside Docker, `localhost` is the container itself; see [Ollama](providers.md#ollama) for `OLLAMA_BASE_URL`.

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
