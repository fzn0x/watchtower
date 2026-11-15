# LLM providers

## Built-in providers

Set one key in `.env`, or sign in to Claude, and Watchtower picks the provider in this order:

| Key | Provider | Model variable | Default model |
| --- | --- | --- | --- |
| `OPENROUTER_API_KEY` | OpenRouter | `OPENROUTER_MODEL_NAME` | `anthropic/claude-sonnet-5.5` |
| `OPENAI_API_KEY` | OpenAI | `OPENAI_MODEL_NAME` | `gpt-5.6` |
| `GEMINI_API_KEY` | Google Gemini | `GEMINI_MODEL_NAME` | `gemini-3.8-flash` |
| Claude credentials ([see below](#claude)) | Anthropic Claude | `ANTHROPIC_MODEL_NAME` | `claude-sonnet-5-5` |

`--flagship` switches Claude to `claude-opus-5-5`.

## Claude

Watchtower uses the Anthropic SDK's own sign-in, so any of these works, checked in this order:

| Method | Set | Use it for |
| --- | --- | --- |
| API key | `ANTHROPIC_API_KEY` | The usual setup. Create a key in the Claude Console. |
| Bearer token | `ANTHROPIC_AUTH_TOKEN`, often with `ANTHROPIC_BASE_URL` | An LLM gateway or proxy in front of the Claude API. |
| Named profile | `ANTHROPIC_PROFILE` | Picking one of several `ant auth login` profiles. |
| Workload identity federation | `ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_ORGANIZATION_ID`, `ANTHROPIC_SERVICE_ACCOUNT_ID`, and `ANTHROPIC_IDENTITY_TOKEN_FILE` | CI and servers, with no long-lived key. |
| Signed in | nothing | Your machine, after `ant auth login`. |

To sign in without managing a key, install the [Anthropic CLI](https://github.com/anthropics/anthropic-cli) and run:

```bash
ant auth login
python -m watchtower.main -t https://www.example.com
```

`ant auth status` shows which credential is active. A leftover `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` in your environment or `.env` takes precedence over the login, so remove it if Watchtower is not using the account you expect.

Claude is chosen automatically when none of the keys in the table above is set. To pick it explicitly, pass `--provider anthropic` (or `--provider claude`); `--model` is optional and `--apikey` is only needed to use a key from a variable with another name.

!!! note "Claude subscriptions"
    Watchtower calls the Claude API, billed to your Claude Console organization. A Claude Pro or Max subscription cannot be used: Anthropic does not allow third-party tools to offer claude.ai login.


## Custom providers

Watchtower supports almost any provider through LangChain and LiteLLM. Override the defaults with `--provider`, `--model`, and `--apikey`:

```bash
python -m watchtower.main -t https://www.example.com \
  --provider=https://api.dgrid.ai/api/v1 \
  --model=anthropic/claude-opus-4.5 \
  --apikey "API_KEY"
```

`--provider` accepts:

- a URL, used as an OpenAI-compatible endpoint (any custom HTTP endpoint works this way, including [local servers](#local-models));
- `ollama`, for a model served by [Ollama](#ollama);
- `openai`, `anthropic` (or `claude`, see [Claude](#claude)), `openrouter`, or `litellm`;
- any other provider name that LangChain's `init_chat_model` understands, with LiteLLM as the fallback.

!!! important
    `--apikey` takes the **name** of the variable that holds your key in `.env` (for example `MY_GROQ_KEY`), not the key itself. This keeps secrets out of your shell history.

The same settings can be put in `.env`:

```ini
WATCHTOWER_PROVIDER="https://api.custom.com/v1"
WATCHTOWER_MODEL="custom-model-v1"
WATCHTOWER_APIKEY_NAME="MY_CUSTOM_KEY"
MY_CUSTOM_KEY="sk-..."
```

Example output (using the `httpx` tool):

```text
INFO: ==> Node Executed: [WORKER]
INFO: HTTP Request: POST https://api.dgrid.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO: ==> Node Executed: [ANALYST]
INFO:     - Updated state 'findings': [{'title': 'Overly Permissive CORS Configuration', 'severity': 'Medium', ...}, {'title': 'Missing Security Headers', 'severity': 'Low', ...}]
```

**Supported providers include:** Anthropic, OpenAI, OpenRouter, LiteLLM, Amazon Bedrock, Vercel AI Gateway, Moonshot AI, Mistral, MiniMax, OpenCode Zen, GLM models, Z.AI, Synthetic, and Qianfan, plus Ollama and any OpenAI-compatible HTTP endpoint. See the full list at [docs.litellm.ai/docs/providers](https://docs.litellm.ai/docs/providers).

## Local models

Watchtower can run on a model served from your own machine, so target data never leaves it. Any server with an OpenAI-compatible API works.

### Ollama

Pull a model, then point Watchtower at Ollama with `--provider ollama`:

```bash
ollama pull llama3.3
python -m watchtower.main -t https://www.example.com --provider ollama --model llama3.3
```

Watchtower talks to `http://localhost:11434/v1`. Set `OLLAMA_BASE_URL` to reach Ollama elsewhere, for example from inside Docker:

```ini
WATCHTOWER_PROVIDER="ollama"
WATCHTOWER_MODEL="llama3.3"
OLLAMA_BASE_URL="http://host.docker.internal:11434/v1"
```

On Linux, `host.docker.internal` needs `--add-host=host.docker.internal:host-gateway` on `docker run`.

`--effort` is passed to Ollama as `reasoning_effort` for models that support it, such as `gpt-oss`.

### LM Studio, llama.cpp, vLLM, and other servers

Pass the server's OpenAI-compatible base URL as the provider. Use the address your server prints when it starts, since default ports differ between servers and versions:

```bash
python -m watchtower.main -t https://www.example.com   --provider http://localhost:1234/v1   --model qwen3-14b
```

`--model` is required for Ollama and URL providers. No API key is needed: without `--apikey`, Watchtower sends a placeholder key, and never your `OPENAI_API_KEY`. If your server does check a key, pass `--apikey` with the name of the variable that holds it.

!!! tip "Context length"
    Watchtower sends tool output to the model, and prompts can be long. Local servers often default to a short context window and drop the start of long prompts without an error. Give the model a larger context: in Ollama, create a model with a higher `num_ctx` in its Modelfile (the OpenAI-compatible API cannot set it per request); in other servers, use their context-size setting. Larger models also follow Watchtower's JSON format more reliably.

## Flagship models and reasoning

See [Usage: flagship models and reasoning](usage.md#flagship-models-and-reasoning) for `--flagship`, `--effort`, and `--max-tokens`.
