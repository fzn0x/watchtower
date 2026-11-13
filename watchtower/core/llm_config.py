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
    "openrouter": "anthropic/claude-opus-5.5",
    "anthropic": "claude-opus-5-5",
    "gemini": "gemini-4-carbon",
}

# Effort levels the CLI accepts, lowest to highest.
EFFORT_LEVELS = ["low", "medium", "high", "xhigh", "max"]

# Full ordering used for clamping, including levels some providers add below "low".
_EFFORT_ORDER = ["minimal", "low", "medium", "high", "xhigh", "max"]

# Effort levels each provider family accepts. Families not listed fall back to
# the commonly documented low/medium/high.
SUPPORTED_EFFORTS = {
    "anthropic": ["low", "medium", "high", "xhigh", "max"],
    "gemini": ["minimal", "low", "medium", "high"],
}
_DEFAULT_SUPPORTED_EFFORTS = ["low", "medium", "high"]

# Effort used when --flagship is set without an explicit --effort.
FLAGSHIP_DEFAULT_EFFORT = "high"

# Output budget when reasoning is on and --max-tokens is not set. Enough for
# thinking plus Watchtower's short JSON replies, and well under the point where
# non-streaming requests risk timeouts.
DEFAULT_REASONING_MAX_TOKENS = 16000

# Families whose reasoning is set through OpenAI-compatible extra_body rather
# than the native reasoning_effort constructor argument.
_EXTRA_BODY_FAMILIES = {"openrouter", "http"}


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


# Environment variables that select a provider in get_llm, in priority order
# after a custom WATCHTOWER_PROVIDER.
PROVIDER_KEY_VARS = ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")

NO_PROVIDER_MESSAGE = (
    "No LLM provider is configured. Set one of OPENROUTER_API_KEY, OPENAI_API_KEY, "
    "or GEMINI_API_KEY in .env, or pass --provider, --model, and --apikey."
)


def has_provider(env=None) -> bool:
    """True if get_llm can build a model: a custom provider or a provider key is set."""
    env = os.environ if env is None else env
    if (env.get("WATCHTOWER_PROVIDER") or "").strip():
        return True
    return any((env.get(name) or "").strip() for name in PROVIDER_KEY_VARS)


def read_llm_runtime(env=None) -> dict:
    """Read reasoning runtime settings from the environment into a plain dict.

    Unknown effort values are ignored rather than passed to a provider.
    """
    env = os.environ if env is None else env
    max_tokens_raw = env.get("WATCHTOWER_MAX_TOKENS")
    try:
        max_tokens = int(max_tokens_raw) if max_tokens_raw else None
    except (TypeError, ValueError):
        max_tokens = None
    effort = (env.get("WATCHTOWER_EFFORT") or "").strip().lower() or None
    if effort not in _EFFORT_ORDER:
        effort = None
    return {
        "flagship": _truthy(env.get("WATCHTOWER_FLAGSHIP", "")),
        "effort": effort,
        "max_tokens": max_tokens,
    }


def resolve_effort(effort, flagship):
    """Requested reasoning effort: explicit wins, else high when flagship, else None."""
    if effort:
        return effort
    if flagship:
        return FLAGSHIP_DEFAULT_EFFORT
    return None


def clamp_effort(family, effort):
    """Clamp an effort level to the highest level the provider family accepts.

    Returns the level unchanged when supported, otherwise the highest supported
    level at or below it (or the lowest supported level if none is below).
    """
    if effort is None:
        return None
    supported = SUPPORTED_EFFORTS.get(family, _DEFAULT_SUPPORTED_EFFORTS)
    if effort in supported:
        return effort
    if effort not in _EFFORT_ORDER:
        return None
    rank = _EFFORT_ORDER.index(effort)
    at_or_below = [level for level in supported if _EFFORT_ORDER.index(level) <= rank]
    return at_or_below[-1] if at_or_below else supported[0]


def effort_notice(family, effort, flagship):
    """A one-line notice when the requested effort was lowered for this provider, else None."""
    requested = resolve_effort(effort, flagship)
    effective = clamp_effort(family, requested)
    if requested and effective != requested:
        return (f"Reasoning effort '{requested}' is not supported by the {family} provider; "
                f"using '{effective}' instead.")
    return None


def select_model(family, configured_model, flagship):
    """Pick the model id: flagship override when requested, else the configured model."""
    if flagship and family in FLAGSHIP_MODELS:
        return FLAGSHIP_MODELS[family]
    return configured_model


def build_chat_kwargs(family, effort=None, max_tokens=None, flagship=False, default_temperature=0):
    """Build chat-model kwargs (minus model/api_key/base_url) for a provider family.

    When reasoning is on (an effort resolves), temperature is omitted because
    reasoning and flagship models reject a forced temperature, the effort is
    clamped to what the provider accepts, max_tokens defaults to a reasoning
    budget, and the provider's reasoning parameter is attached. When reasoning
    is off, the deterministic default temperature is kept for backward
    compatibility.
    """
    effective_effort = clamp_effort(family, resolve_effort(effort, flagship))
    kwargs = {}

    if effective_effort is None:
        kwargs["temperature"] = default_temperature
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        return kwargs

    kwargs["max_tokens"] = max_tokens or DEFAULT_REASONING_MAX_TOKENS
    if family in _EXTRA_BODY_FAMILIES:
        kwargs["extra_body"] = {"reasoning": {"effort": effective_effort}}
    else:
        kwargs["reasoning_effort"] = effective_effort
    return kwargs
