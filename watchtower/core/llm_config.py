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

# Families that must not be sent a temperature. Current Claude models reject
# any non-default sampling setting with a 400.
_NO_TEMPERATURE_FAMILIES = {"anthropic"}

# Local models. Ollama serves an OpenAI-compatible API here by default; any
# other local server (LM Studio, llama.cpp, vLLM, ...) is reached through
# --provider <url>.
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434/v1"

# Sent as the API key to Ollama and to custom URL endpoints when --apikey is
# not given. The OpenAI client requires some key; local servers ignore it, and
# it keeps OPENAI_API_KEY from being sent to a third-party endpoint.
PLACEHOLDER_API_KEY = "not-needed"


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


# Environment variables that select a provider in get_llm, in priority order
# after a custom WATCHTOWER_PROVIDER. Claude credentials come last.
PROVIDER_KEY_VARS = ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")

# Environment variables that give the Anthropic SDK a Claude credential. A
# profile from `ant auth login` needs none of them; see claude_signed_in.
CLAUDE_CREDENTIAL_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_PROFILE",
    "ANTHROPIC_FEDERATION_RULE_ID",
)

NO_PROVIDER_MESSAGE = (
    "No LLM provider is configured. Set one of OPENROUTER_API_KEY, OPENAI_API_KEY, "
    "GEMINI_API_KEY, or ANTHROPIC_API_KEY in .env, sign in to Claude with "
    "`ant auth login`, pass --provider, --model, and --apikey, or run a local "
    "model with --provider ollama --model <name>."
)

MODEL_REQUIRED_MESSAGE = (
    "--provider {provider} needs a model name. Pass --model (for example "
    "--model llama3.3) or set WATCHTOWER_MODEL."
)


def needs_explicit_model(provider) -> bool:
    """True for providers with no sensible default model: Ollama and custom URLs."""
    provider = (provider or "").strip().lower()
    return provider == "ollama" or provider.startswith("http")


def claude_signed_in() -> bool:
    """True if the Anthropic SDK finds a Claude credential without environment variables.

    That is the active profile from `ant auth login`. A profile that is set up
    but broken also counts, so the SDK's own error reaches the user instead of
    a generic "no provider" message.
    """
    try:
        from anthropic.lib.credentials import default_credentials
    except Exception:
        return False
    try:
        return default_credentials() is not None
    except Exception:
        return True


def has_claude_credentials(env=None) -> bool:
    """True if Claude can authenticate: a credential variable, or (for the real environment) a login."""
    real_env = env is None
    env = os.environ if env is None else env
    if any((env.get(name) or "").strip() for name in CLAUDE_CREDENTIAL_VARS):
        return True
    return real_env and claude_signed_in()


def has_provider(env=None) -> bool:
    """True if get_llm can build a model: a custom provider, a provider key, or Claude credentials."""
    real_env = env is None
    env = os.environ if env is None else env
    if (env.get("WATCHTOWER_PROVIDER") or "").strip():
        return True
    if any((env.get(name) or "").strip() for name in PROVIDER_KEY_VARS):
        return True
    return has_claude_credentials(None if real_env else env)


def provider_error(env=None):
    """Why get_llm cannot build a model with these settings, or None if it can."""
    real_env = env is None
    env = os.environ if env is None else env
    # None keeps the `ant auth login` check, which only runs for the real environment.
    if not has_provider(None if real_env else env):
        return NO_PROVIDER_MESSAGE
    provider = (env.get("WATCHTOWER_PROVIDER") or "").strip()
    if needs_explicit_model(provider) and not (env.get("WATCHTOWER_MODEL") or "").strip():
        return MODEL_REQUIRED_MESSAGE.format(provider=provider)
    return None


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
    compatibility, except for Claude, which rejects any temperature.
    """
    effective_effort = clamp_effort(family, resolve_effort(effort, flagship))
    kwargs = {}

    if effective_effort is None:
        if family not in _NO_TEMPERATURE_FAMILIES:
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
