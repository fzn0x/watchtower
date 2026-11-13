"""Reasoning-aware LLM configuration.

Pure helpers that decide what to pass to a LangChain chat model, kept separate
from instantiation so the logic can be unit-tested without importing the heavy
provider SDKs.
"""

import os

# Opt-in flagship model per provider family. Balanced defaults stay in get_llm;
# these are only used when --flagship (WATCHTOWER_FLAGSHIP) is set.
FLAGSHIP_MODELS = {
    "openai": "gpt-6-astra",
    "openrouter": "anthropic/claude-opus-5",
    "anthropic": "claude-opus-5",
    "gemini": "gemini-4-carbon",
}

# Effort levels the CLI accepts. Providers accept a subset (for example the
# OpenAI reasoning models take low/medium/high); values outside a provider's
# range are passed through and may be rejected by that provider.
EFFORT_LEVELS = ["low", "medium", "high", "xhigh", "max"]

# Effort used when --flagship is set without an explicit --effort.
FLAGSHIP_DEFAULT_EFFORT = "high"

# Families whose reasoning is set through OpenAI-compatible extra_body rather
# than the native reasoning_effort constructor argument.
_EXTRA_BODY_FAMILIES = {"openrouter", "http"}


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def read_llm_runtime(env=None) -> dict:
    """Read reasoning runtime settings from the environment into a plain dict."""
    env = os.environ if env is None else env
    max_tokens_raw = env.get("WATCHTOWER_MAX_TOKENS")
    try:
        max_tokens = int(max_tokens_raw) if max_tokens_raw else None
    except (TypeError, ValueError):
        max_tokens = None
    return {
        "flagship": _truthy(env.get("WATCHTOWER_FLAGSHIP", "")),
        "effort": env.get("WATCHTOWER_EFFORT") or None,
        "max_tokens": max_tokens,
    }


def resolve_effort(effort, flagship):
    """Effective reasoning effort: explicit wins, else high when flagship, else None."""
    if effort:
        return effort
    if flagship:
        return FLAGSHIP_DEFAULT_EFFORT
    return None


def select_model(family, configured_model, flagship):
    """Pick the model id: flagship override when requested, else the configured model."""
    if flagship and family in FLAGSHIP_MODELS:
        return FLAGSHIP_MODELS[family]
    return configured_model


def build_chat_kwargs(family, effort=None, max_tokens=None, flagship=False, default_temperature=0):
    """Build chat-model kwargs (minus model/api_key/base_url) for a provider family.

    When reasoning is on (an effort resolves), temperature is omitted because
    reasoning and flagship models reject a forced temperature, and the provider's
    reasoning parameter is attached. When reasoning is off, the deterministic
    default temperature is kept for backward compatibility.
    """
    effective_effort = resolve_effort(effort, flagship)
    kwargs = {}

    if effective_effort is None:
        kwargs["temperature"] = default_temperature

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    if effective_effort is not None:
        if family in _EXTRA_BODY_FAMILIES:
            kwargs["extra_body"] = {"reasoning": {"effort": effective_effort}}
        else:
            kwargs["reasoning_effort"] = effective_effort

    return kwargs
