import os
import unittest
from unittest import mock

from watchtower.core.llm_config import (
    CLAUDE_CREDENTIAL_VARS,
    MODEL_REQUIRED_MESSAGE,
    NO_PROVIDER_MESSAGE,
    OLLAMA_DEFAULT_BASE_URL,
    PLACEHOLDER_API_KEY,
    PROVIDER_KEY_VARS,
    needs_explicit_model,
    provider_error,
)

try:
    import langchain_openai  # noqa: F401
    _HAS_LANGCHAIN = True
except Exception:
    _HAS_LANGCHAIN = False

_LLM_VARS = set(PROVIDER_KEY_VARS) | set(CLAUDE_CREDENTIAL_VARS) | {
    "WATCHTOWER_PROVIDER", "WATCHTOWER_MODEL", "WATCHTOWER_APIKEY_NAME",
    "WATCHTOWER_FLAGSHIP", "WATCHTOWER_EFFORT", "WATCHTOWER_MAX_TOKENS",
    "OLLAMA_BASE_URL",
}


def _clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in _LLM_VARS}
    env.update(extra)
    return env


class ProviderErrorTests(unittest.TestCase):
    def test_nothing_configured(self):
        self.assertEqual(provider_error({}), NO_PROVIDER_MESSAGE)

    def test_ollama_needs_a_model(self):
        self.assertEqual(
            provider_error({"WATCHTOWER_PROVIDER": "ollama"}),
            MODEL_REQUIRED_MESSAGE.format(provider="ollama"),
        )

    def test_url_needs_a_model(self):
        url = "http://localhost:1234/v1"
        self.assertEqual(
            provider_error({"WATCHTOWER_PROVIDER": url, "WATCHTOWER_MODEL": " "}),
            MODEL_REQUIRED_MESSAGE.format(provider=url),
        )

    def test_ok_with_a_model(self):
        self.assertIsNone(provider_error({"WATCHTOWER_PROVIDER": "ollama", "WATCHTOWER_MODEL": "llama3.3"}))

    def test_hosted_providers_keep_their_default_model(self):
        self.assertIsNone(provider_error({"WATCHTOWER_PROVIDER": "openai"}))
        self.assertIsNone(provider_error({"OPENAI_API_KEY": "x"}))

    def test_real_environment_keeps_the_claude_login_check(self):
        # provider_error() must let has_provider look for an `ant auth login`
        # profile, which it only does for the real environment.
        with mock.patch.dict(os.environ, _clean_env(), clear=True):
            with mock.patch("watchtower.core.llm_config.claude_signed_in", return_value=True):
                self.assertIsNone(provider_error())
            with mock.patch("watchtower.core.llm_config.claude_signed_in", return_value=False):
                self.assertEqual(provider_error(), NO_PROVIDER_MESSAGE)

    def test_needs_explicit_model(self):
        self.assertTrue(needs_explicit_model("Ollama"))
        self.assertTrue(needs_explicit_model("https://example.test/v1"))
        self.assertFalse(needs_explicit_model("anthropic"))
        self.assertFalse(needs_explicit_model(None))


@unittest.skipUnless(_HAS_LANGCHAIN, "langchain-openai is not installed in this environment")
class LocalGetLlmTests(unittest.TestCase):
    def _llm(self, **env):
        from watchtower.agents import planner

        with mock.patch.dict(os.environ, _clean_env(**env), clear=True):
            return planner.get_llm()

    def test_ollama_uses_the_default_local_endpoint(self):
        llm = self._llm(WATCHTOWER_PROVIDER="ollama", WATCHTOWER_MODEL="llama3.3")
        self.assertEqual(llm.model_name, "llama3.3")
        self.assertEqual(llm.openai_api_base, OLLAMA_DEFAULT_BASE_URL)
        self.assertEqual(llm.openai_api_key.get_secret_value(), PLACEHOLDER_API_KEY)

    def test_ollama_base_url_can_be_overridden(self):
        url = "http://host.docker.internal:11434/v1"
        llm = self._llm(WATCHTOWER_PROVIDER="ollama", WATCHTOWER_MODEL="qwen3", OLLAMA_BASE_URL=url)
        self.assertEqual(llm.openai_api_base, url)

    def test_ollama_passes_reasoning_effort(self):
        llm = self._llm(WATCHTOWER_PROVIDER="ollama", WATCHTOWER_MODEL="gpt-oss:20b", WATCHTOWER_EFFORT="high")
        self.assertEqual(llm.reasoning_effort, "high")

    def test_url_provider_does_not_send_the_openai_key(self):
        # Regression: without --apikey, ChatOpenAI fell back to OPENAI_API_KEY
        # and sent it to the custom endpoint.
        llm = self._llm(
            WATCHTOWER_PROVIDER="http://localhost:1234/v1",
            WATCHTOWER_MODEL="qwen3",
            OPENAI_API_KEY="sk-real-openai-key",
        )
        self.assertEqual(llm.openai_api_base, "http://localhost:1234/v1")
        self.assertEqual(llm.openai_api_key.get_secret_value(), PLACEHOLDER_API_KEY)

    def test_url_provider_uses_the_named_key(self):
        llm = self._llm(
            WATCHTOWER_PROVIDER="https://llm.example.test/v1",
            WATCHTOWER_MODEL="m",
            WATCHTOWER_APIKEY_NAME="MY_KEY",
            MY_KEY="sk-mine",
        )
        self.assertEqual(llm.openai_api_key.get_secret_value(), "sk-mine")

    def test_missing_model_is_a_clear_error(self):
        with self.assertRaises(RuntimeError) as ctx:
            self._llm(WATCHTOWER_PROVIDER="ollama")
        self.assertEqual(str(ctx.exception), MODEL_REQUIRED_MESSAGE.format(provider="ollama"))


if __name__ == "__main__":
    unittest.main()
