import os
import unittest
from unittest import mock

from watchtower.core.claude import CLAUDE_DEFAULT_MODEL
from watchtower.core.llm_config import (
    CLAUDE_CREDENTIAL_VARS,
    FLAGSHIP_MODELS,
    PROVIDER_KEY_VARS,
    claude_signed_in,
    has_claude_credentials,
    has_provider,
)

try:
    import langchain_anthropic  # noqa: F401
    import langchain_openai  # noqa: F401
    _HAS_LANGCHAIN = True
except Exception:
    _HAS_LANGCHAIN = False

_LLM_VARS = set(PROVIDER_KEY_VARS) | set(CLAUDE_CREDENTIAL_VARS) | {
    "WATCHTOWER_PROVIDER", "WATCHTOWER_MODEL", "WATCHTOWER_APIKEY_NAME",
    "WATCHTOWER_FLAGSHIP", "WATCHTOWER_EFFORT", "WATCHTOWER_MAX_TOKENS",
    "ANTHROPIC_MODEL_NAME", "ANTHROPIC_BASE_URL", "ANTHROPIC_API_URL",
    "ANTHROPIC_CONFIG_DIR",
}


def _clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in _LLM_VARS}
    env.update(extra)
    return env


class ClaudeCredentialTests(unittest.TestCase):
    def test_each_credential_variable_counts(self):
        for name in CLAUDE_CREDENTIAL_VARS:
            with self.subTest(var=name):
                self.assertTrue(has_claude_credentials({name: "x"}))
                self.assertTrue(has_provider({name: "x"}))

    def test_blank_variables_do_not_count(self):
        self.assertFalse(has_claude_credentials({"ANTHROPIC_API_KEY": " ", "ANTHROPIC_AUTH_TOKEN": ""}))

    def test_a_given_env_never_reads_the_disk(self):
        with mock.patch("watchtower.core.llm_config.claude_signed_in", return_value=True) as signed_in:
            self.assertFalse(has_claude_credentials({}))
        signed_in.assert_not_called()

    def test_ant_auth_login_counts_as_a_provider(self):
        with mock.patch.dict(os.environ, _clean_env(), clear=True), \
                mock.patch("watchtower.core.llm_config.claude_signed_in", return_value=True):
            self.assertTrue(has_provider())

    def test_signed_in_follows_the_sdk(self):
        with mock.patch("anthropic.lib.credentials.default_credentials", return_value=object()):
            self.assertTrue(claude_signed_in())
        with mock.patch("anthropic.lib.credentials.default_credentials", return_value=None):
            self.assertFalse(claude_signed_in())

    def test_a_broken_login_still_counts(self):
        # The SDK's own error explains a broken profile better than "no provider".
        with mock.patch("anthropic.lib.credentials.default_credentials", side_effect=ValueError("bad profile")):
            self.assertTrue(claude_signed_in())


@unittest.skipUnless(_HAS_LANGCHAIN, "langchain-anthropic is not installed in this environment")
class ClaudeGetLlmTests(unittest.TestCase):
    def _llm(self, signed_in=False, **env):
        from watchtower.agents import planner

        with mock.patch.dict(os.environ, _clean_env(**env), clear=True), \
                mock.patch("watchtower.core.llm_config.claude_signed_in", return_value=signed_in):
            llm = planner.get_llm()
            # Build the SDK client inside the patched environment, as a run would.
            client = llm._client if llm.__class__.__name__ == "WatchtowerChatAnthropic" else None
        return llm, client

    def test_api_key_is_used(self):
        llm, client = self._llm(ANTHROPIC_API_KEY="sk-ant-test")
        self.assertEqual(llm.model, CLAUDE_DEFAULT_MODEL)
        self.assertEqual(client.api_key, "sk-ant-test")

    def test_auth_token_reaches_the_sdk(self):
        # Regression: ChatAnthropic passed api_key="" and the SDK never looked
        # at ANTHROPIC_AUTH_TOKEN.
        llm, client = self._llm(ANTHROPIC_AUTH_TOKEN="gateway-token", ANTHROPIC_BASE_URL="https://gateway.example.test")
        self.assertIsNone(client.api_key)
        self.assertEqual(client.auth_token, "gateway-token")
        self.assertEqual(str(client.base_url).rstrip("/"), "https://gateway.example.test")

    def test_signed_in_profile_selects_claude(self):
        # With only an `ant auth login` profile, Claude is chosen and the SDK
        # is left to load the profile (no key or token is passed).
        fake = mock.Mock(provider=None, extra_headers={}, base_url=None)
        with mock.patch("anthropic.lib.credentials.default_credentials", return_value=fake):
            llm, client = self._llm(signed_in=True)
        self.assertEqual(llm.__class__.__name__, "WatchtowerChatAnthropic")
        self.assertIsNone(llm._client_params["api_key"])
        self.assertIsNone(llm._client_params["base_url"])

    def test_model_name_and_flagship(self):
        llm, _ = self._llm(ANTHROPIC_API_KEY="k", ANTHROPIC_MODEL_NAME="claude-haiku-5-5")
        self.assertEqual(llm.model, "claude-haiku-5-5")
        llm, _ = self._llm(ANTHROPIC_API_KEY="k", WATCHTOWER_FLAGSHIP="1")
        self.assertEqual(llm.model, FLAGSHIP_MODELS["anthropic"])
        self.assertEqual(llm.reasoning_effort, "high")

    def test_no_temperature_is_sent(self):
        llm, _ = self._llm(ANTHROPIC_API_KEY="k")
        self.assertIsNone(llm.temperature)

    def test_other_providers_keep_priority(self):
        llm, _ = self._llm(OPENAI_API_KEY="sk-openai", ANTHROPIC_API_KEY="sk-ant")
        self.assertEqual(llm.__class__.__name__, "ChatOpenAI")

    def test_provider_flag_without_model_uses_the_claude_default(self):
        for name in ("anthropic", "claude"):
            with self.subTest(provider=name):
                llm, client = self._llm(WATCHTOWER_PROVIDER=name, ANTHROPIC_AUTH_TOKEN="t")
                self.assertEqual(llm.model, CLAUDE_DEFAULT_MODEL)
                self.assertEqual(client.auth_token, "t")

    def test_provider_flag_with_named_key(self):
        llm, client = self._llm(
            WATCHTOWER_PROVIDER="anthropic", WATCHTOWER_MODEL="claude-opus-5-5",
            WATCHTOWER_APIKEY_NAME="MY_CLAUDE_KEY", MY_CLAUDE_KEY="sk-ant-mine",
        )
        self.assertEqual(llm.model, "claude-opus-5-5")
        self.assertEqual(client.api_key, "sk-ant-mine")


if __name__ == "__main__":
    unittest.main()
