import os
import unittest
from unittest import mock

from watchtower.core.llm_config import NO_PROVIDER_MESSAGE, PROVIDER_KEY_VARS, has_provider

try:
    import langchain_core  # noqa: F401
    _HAS_LANGCHAIN = True
except Exception:
    _HAS_LANGCHAIN = False


def _env_without_providers():
    drop = set(PROVIDER_KEY_VARS) | {"WATCHTOWER_PROVIDER"}
    return {k: v for k, v in os.environ.items() if k not in drop}


class HasProviderTests(unittest.TestCase):
    def test_false_when_nothing_is_set(self):
        self.assertFalse(has_provider({}))

    def test_blank_values_do_not_count(self):
        self.assertFalse(has_provider({"OPENAI_API_KEY": "  ", "WATCHTOWER_PROVIDER": ""}))

    def test_each_provider_key_counts(self):
        for name in PROVIDER_KEY_VARS:
            with self.subTest(key=name):
                self.assertTrue(has_provider({name: "x"}))

    def test_custom_provider_counts(self):
        self.assertTrue(has_provider({"WATCHTOWER_PROVIDER": "anthropic"}))


@unittest.skipUnless(_HAS_LANGCHAIN, "langchain is not installed in this environment")
class NoProviderTests(unittest.TestCase):
    def test_get_llm_raises_a_clear_error(self):
        # Regression: this used to return a MockLLM that could not be piped
        # into the output parser, so runs failed with an opaque error.
        from watchtower.agents import planner

        with mock.patch.dict(os.environ, _env_without_providers(), clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                planner.get_llm()
        self.assertEqual(str(ctx.exception), NO_PROVIDER_MESSAGE)

    def test_planner_reports_it_and_finishes(self):
        from watchtower.agents import planner

        with mock.patch.dict(os.environ, _env_without_providers(), clear=True):
            result = planner.planner_node({"scope_targets": ["http://t"], "available_tools": []})
        self.assertTrue(result["is_finished"])
        self.assertIn("No LLM provider is configured", result["current_plan"])


if __name__ == "__main__":
    unittest.main()
