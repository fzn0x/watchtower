"""Claude chat model that authenticates the way the Anthropic SDK does.

LangChain's ChatAnthropic always hands the SDK an API key, an empty string
when none is set, and the SDK treats any key it is given as the credential to
use. That hides every other sign-in method. This subclass passes no key when
there is none, so the SDK resolves credentials itself, in its documented
order: ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, the profile named by
ANTHROPIC_PROFILE, workload identity federation, then the active profile from
`ant auth login`.
"""

import os
from functools import cached_property

CLAUDE_DEFAULT_MODEL = "claude-sonnet-5-5"

_DEFAULT_API_URL = "https://api.anthropic.com"
_BASE_URL_VARS = ("ANTHROPIC_API_URL", "ANTHROPIC_BASE_URL")

_chat_class = None


def chat_anthropic_class():
    """The ChatAnthropic subclass, built on first use so importing this module stays light."""
    global _chat_class
    if _chat_class is None:
        from langchain_anthropic import ChatAnthropic

        class WatchtowerChatAnthropic(ChatAnthropic):
            @cached_property
            def _client_params(self):
                params = dict(super()._client_params)
                if not params.get("api_key"):
                    params["api_key"] = None
                # ChatAnthropic fills in the public endpoint when no base URL is
                # set. Dropping it lets a profile's own base URL apply.
                if params.get("base_url") == _DEFAULT_API_URL and not any(
                    os.getenv(name) for name in _BASE_URL_VARS
                ):
                    params["base_url"] = None
                return params

        _chat_class = WatchtowerChatAnthropic
    return _chat_class


def make_chat_anthropic(model, api_key=None, **kwargs):
    """A Claude chat model. Pass api_key only to override the SDK's own lookup."""
    if api_key:
        kwargs["api_key"] = api_key
    return chat_anthropic_class()(model_name=model, **kwargs)
