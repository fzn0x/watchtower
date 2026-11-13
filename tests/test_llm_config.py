import unittest

from watchtower.core.llm_config import (
    FLAGSHIP_MODELS,
    build_chat_kwargs,
    read_llm_runtime,
    resolve_effort,
    select_model,
)


class ReadRuntimeTests(unittest.TestCase):
    def test_defaults_when_unset(self):
        rt = read_llm_runtime({})
        self.assertEqual(rt, {"flagship": False, "effort": None, "max_tokens": None})

    def test_parses_values(self):
        rt = read_llm_runtime({
            "WATCHTOWER_FLAGSHIP": "1",
            "WATCHTOWER_EFFORT": "high",
            "WATCHTOWER_MAX_TOKENS": "8000",
        })
        self.assertEqual(rt, {"flagship": True, "effort": "high", "max_tokens": 8000})

    def test_flagship_truthy_variants(self):
        for val in ("1", "true", "YES", "on"):
            self.assertTrue(read_llm_runtime({"WATCHTOWER_FLAGSHIP": val})["flagship"])
        for val in ("0", "false", "", "no"):
            self.assertFalse(read_llm_runtime({"WATCHTOWER_FLAGSHIP": val})["flagship"])

    def test_bad_max_tokens_is_none(self):
        self.assertIsNone(read_llm_runtime({"WATCHTOWER_MAX_TOKENS": "lots"})["max_tokens"])


class ResolveEffortTests(unittest.TestCase):
    def test_explicit_wins(self):
        self.assertEqual(resolve_effort("medium", True), "medium")

    def test_flagship_defaults_high(self):
        self.assertEqual(resolve_effort(None, True), "high")

    def test_none_when_off(self):
        self.assertIsNone(resolve_effort(None, False))


class SelectModelTests(unittest.TestCase):
    def test_flagship_override_per_family(self):
        self.assertEqual(select_model("openai", "gpt-5.6", True), FLAGSHIP_MODELS["openai"])
        self.assertEqual(select_model("openrouter", "x", True), FLAGSHIP_MODELS["openrouter"])
        self.assertEqual(select_model("gemini", "x", True), FLAGSHIP_MODELS["gemini"])

    def test_configured_model_when_not_flagship(self):
        self.assertEqual(select_model("openai", "gpt-5.6", False), "gpt-5.6")

    def test_unknown_family_passthrough_even_if_flagship(self):
        self.assertEqual(select_model("litellm", "some-model", True), "some-model")


class BuildChatKwargsTests(unittest.TestCase):
    def test_reasoning_off_keeps_temperature(self):
        self.assertEqual(build_chat_kwargs("openai"), {"temperature": 0})

    def test_max_tokens_included(self):
        self.assertEqual(
            build_chat_kwargs("openai", max_tokens=4096),
            {"temperature": 0, "max_tokens": 4096},
        )

    def test_openai_effort_uses_reasoning_effort_and_drops_temperature(self):
        kwargs = build_chat_kwargs("openai", effort="high")
        self.assertEqual(kwargs, {"reasoning_effort": "high"})
        self.assertNotIn("temperature", kwargs)

    def test_openrouter_effort_uses_extra_body(self):
        kwargs = build_chat_kwargs("openrouter", effort="high")
        self.assertEqual(kwargs, {"extra_body": {"reasoning": {"effort": "high"}}})

    def test_http_family_uses_extra_body(self):
        self.assertEqual(
            build_chat_kwargs("http", effort="medium"),
            {"extra_body": {"reasoning": {"effort": "medium"}}},
        )

    def test_anthropic_and_gemini_use_reasoning_effort(self):
        self.assertEqual(build_chat_kwargs("anthropic", effort="low"), {"reasoning_effort": "low"})
        self.assertEqual(build_chat_kwargs("gemini", effort="low"), {"reasoning_effort": "low"})

    def test_flagship_turns_reasoning_on_at_high(self):
        self.assertEqual(build_chat_kwargs("openai", flagship=True), {"reasoning_effort": "high"})
        self.assertEqual(
            build_chat_kwargs("openrouter", flagship=True),
            {"extra_body": {"reasoning": {"effort": "high"}}},
        )

    def test_effort_with_max_tokens(self):
        self.assertEqual(
            build_chat_kwargs("openai", effort="high", max_tokens=16000),
            {"max_tokens": 16000, "reasoning_effort": "high"},
        )


if __name__ == "__main__":
    unittest.main()
