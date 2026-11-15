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

- a URL, used as an OpenAI-compatible endpoint (any custom HTTP endpoint works this way);
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

**Supported providers include:** Anthropic, OpenAI, OpenRouter, LiteLLM, Amazon Bedrock, Vercel AI Gateway, Moonshot AI, Mistral, MiniMax, OpenCode Zen, GLM models, Z.AI, Synthetic, and Qianfan, plus any OpenAI-compatible HTTP endpoint. See the full list at [docs.litellm.ai/docs/providers](https://docs.litellm.ai/docs/providers).

## Flagship models and reasoning

See [Usage: flagship models and reasoning](usage.md#flagship-models-and-reasoning) for `--flagship`, `--effort`, and `--max-tokens`.
