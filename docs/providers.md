# LLM providers

## Built-in providers

Set one key in `.env` and Watchtower picks the provider in this order:

| Key | Provider | Model variable | Default model |
| --- | --- | --- | --- |
| `OPENROUTER_API_KEY` | OpenRouter | `OPENROUTER_MODEL_NAME` | `anthropic/claude-sonnet-5.5` |
| `OPENAI_API_KEY` | OpenAI | `OPENAI_MODEL_NAME` | `gpt-5.6` |
| `GEMINI_API_KEY` | Google Gemini | `GEMINI_MODEL_NAME` | `gemini-3.8-flash` |

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
- `openai`, `anthropic`, `openrouter`, or `litellm`;
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
