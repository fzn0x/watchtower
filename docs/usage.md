# Usage

Give Watchtower a target URL or IP with `-t` / `--target`:

```bash
python -m watchtower.main -t https://www.example.com
```

Print the installed version with `--version`.

## Interactive tool selection

On launch, Watchtower shows a checklist of the supported tools with the installed ones pre-selected. Use ++space++ to toggle tools (narrowing what the planner may run) and ++enter++ to confirm.

## Headless mode

To skip the checklist (for example in CI), use `--skip-ask-tools`. Watchtower then offers the planner every supported tool installed on your `PATH`; missing tools are logged and left out.

```bash
python -m watchtower.main -t https://www.example.com --skip-ask-tools
```

## Authenticated testing

Pass a session cookie or custom headers for authenticated workflows:

```bash
python -m watchtower.main -t https://api.example.com \
  --cookie "session=xyz123" \
  --header "X-API-Key: secret-key"
```

`--header` can be repeated.

## Flagship models and reasoning

Watchtower defaults to balanced, cost-effective models. For harder targets, opt into the provider's flagship model and turn on reasoning:

```bash
# Flagship model for your provider, reasoning at high effort
python -m watchtower.main -t https://www.example.com --flagship

# Or tune reasoning effort and the output budget directly
python -m watchtower.main -t https://www.example.com --effort high --max-tokens 8000
```

- `--flagship` selects the provider's top model (for example `gpt-6-astra`, `gemini-4-carbon`, `claude-opus-5-5`, or `anthropic/claude-opus-5.5` on OpenRouter) and runs it at high effort.
- `--effort` accepts `low`, `medium`, `high`, `xhigh`, `max`. Watchtower lowers the value to the highest level each provider supports and logs a notice when it does: Anthropic accepts the full range, while OpenAI, OpenRouter, Gemini, and LiteLLM top out at `high`.
- `--max-tokens` caps the output tokens. When reasoning is on and this is not set, it defaults to 16000.

When reasoning is on, Watchtower omits the `temperature` setting, since flagship and reasoning models reject a forced temperature. The same settings can be put in `.env` as `WATCHTOWER_FLAGSHIP`, `WATCHTOWER_EFFORT`, and `WATCHTOWER_MAX_TOKENS`.

!!! note
    Flagship ids and reasoning parameters change often across providers. If a model or effort value is rejected, set a current one for your provider.

## Important notes

- **API costs**: the agents call the model on every step while the planner loops through observations. Watch your API budget.
- **Hallucinations**: the analyst filters false positives, but LLMs can still misread ambiguous tool output. **Always verify findings manually.**
- **Noisy tools**: some tools (`masscan`, `ffuf`) are very noisy and can trip edge protections such as Cloudflare, which fills the logs with `403` responses.
