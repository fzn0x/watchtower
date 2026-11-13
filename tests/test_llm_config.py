import unittest

from watchtower.core.llm_config import (
    DEFAULT_REASONING_MAX_TOKENS,
    FLAGSHIP_MODELS,
    build_chat_kwargs,
    clamp_effort,
    effort_notice,
    read_llm_runtime,
    resolve_effort,
    select_model,
)

R = DEFAULT_REASONING_MAX_TOKENS


class ReadRuntimeTests(unittest.TestCase):
    def test_defaults_when_unset(self):
        self.assertEqual(read_llm_runtime({}), {"flagship": False, "effort": None, "max_tokens": None})

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

    def test_effort_is_normalized(self):
        self.assertEqual(read_llm_runtime({"WATCHTOWER_EFFORT": " HIGH "})["effort"], "high")

    def test_unknown_effort_is_ignored(self):
        self.assertIsNone(read_llm_runtime({"WATCHTOWER_EFFORT": "turbo"})["effort"])


class ResolveEffortTests(unittest.TestCase):
    def test_explicit_wins(self):
        self.assertEqual(resolve_effort("medium", True), "medium")

    def test_flagship_defaults_high(self):
        self.assertEqual(resolve_effort(None, True), "high")

    def test_none_when_off(self):
        self.assertIsNone(resolve_effort(None, False))


class ClampEffortTests(unittest.TestCase):
    def test_gemini_caps_at_high(self):
        # Gemini rejects xhigh/max at construction; this was a crash in 1.0.5.
        self.assertEqual(clamp_effort("gemini", "max"), "high")
        self.assertEqual(clamp_effort("gemini", "xhigh"), "high")
        self.assertEqual(clamp_effort("gemini", "medium"), "medium")

    def test_anthropic_keeps_full_range(self):
        for level in ("low", "medium", "high", "xhigh", "max"):
            self.assertEqual(clamp_effort("anthropic", level), level)

    def test_openai_compatible_families_cap_at_high(self):
        for family in ("openai", "openrouter", "http", "litellm", "generic"):
            self.assertEqual(clamp_effort(family, "max"), "high")
            self.assertEqual(clamp_effort(family, "xhigh"), "high")

    def test_below_supported_range_uses_lowest(self):
        self.assertEqual(clamp_effort("openai", "minimal"), "low")

    def test_none_and_unknown(self):
        self.assertIsNone(clamp_effort("openai", None))
        self.assertIsNone(clamp_effort("openai", "turbo"))


class EffortNoticeTests(unittest.TestCase):
    def test_notice_when_lowered(self):
        msg = effort_notice("gemini", "max", False)
        self.assertIn("'max'", msg)
        self.assertIn("'high'", msg)

    def test_no_notice_when_supported(self):
        self.assertIsNone(effort_notice("anthropic", "max", False))
        self.assertIsNone(effort_notice("openai", "high", False))
        self.assertIsNone(effort_notice("gemini", None, True))  # flagship default is high
        self.assertIsNone(effort_notice("openai", None, False))


class SelectModelTests(unittest.TestCase):
    def test_flagship_override_per_family(self):
        self.assertEqual(select_model("openai", "gpt-5.6", True), FLAGSHIP_MODELS["openai"])
        self.assertEqual(select_model("openrouter", "x", True), "anthropic/claude-opus-5.5")
        self.assertEqual(select_model("anthropic", "x", True), "claude-opus-5-5")
        self.assertEqual(select_model("gemini", "x", True), FLAGSHIP_MODELS["gemini"])

    def test_configured_model_when_not_flagship(self):
        self.assertEqual(select_model("openai", "gpt-5.6", False), "gpt-5.6")

    def test_unknown_family_passthrough_even_if_flagship(self):
        self.assertEqual(select_model("litellm", "some-model", True), "some-model")


class BuildChatKwargsTests(unittest.TestCase):
    def test_reasoning_off_keeps_temperature(self):
        self.assertEqual(build_chat_kwargs("openai"), {"temperature": 0})

    def test_reasoning_off_max_tokens_only_when_given(self):
        self.assertEqual(build_chat_kwargs("openai", max_tokens=4096), {"temperature": 0, "max_tokens": 4096})

    def test_openai_effort(self):
        kwargs = build_chat_kwargs("openai", effort="high")
        self.assertEqual(kwargs, {"max_tokens": R, "reasoning_effort": "high"})
        self.assertNotIn("temperature", kwargs)

    def test_openrouter_effort_uses_extra_body(self):
        self.assertEqual(
            build_chat_kwargs("openrouter", effort="high"),
            {"max_tokens": R, "extra_body": {"reasoning": {"effort": "high"}}},
        )

    def test_http_family_uses_extra_body(self):
        self.assertEqual(
            build_chat_kwargs("http", effort="medium"),
            {"max_tokens": R, "extra_body": {"reasoning": {"effort": "medium"}}},
        )

    def test_anthropic_and_gemini_use_reasoning_effort(self):
        self.assertEqual(build_chat_kwargs("anthropic", effort="low"), {"max_tokens": R, "reasoning_effort": "low"})
        self.assertEqual(build_chat_kwargs("gemini", effort="low"), {"max_tokens": R, "reasoning_effort": "low"})

    def test_flagship_turns_reasoning_on_at_high(self):
        self.assertEqual(build_chat_kwargs("openai", flagship=True), {"max_tokens": R, "reasoning_effort": "high"})
        self.assertEqual(
            build_chat_kwargs("openrouter", flagship=True),
            {"max_tokens": R, "extra_body": {"reasoning": {"effort": "high"}}},
        )

    def test_explicit_max_tokens_wins_over_reasoning_default(self):
        self.assertEqual(
            build_chat_kwargs("anthropic", effort="max", max_tokens=32000),
            {"max_tokens": 32000, "reasoning_effort": "max"},
        )

    def test_effort_is_clamped_in_kwargs(self):
        self.assertEqual(build_chat_kwargs("gemini", effort="max"), {"max_tokens": R, "reasoning_effort": "high"})
        self.assertEqual(
            build_chat_kwargs("openrouter", effort="xhigh"),
            {"max_tokens": R, "extra_body": {"reasoning": {"effort": "high"}}},
        )


if __name__ == "__main__":
    unittest.main()
