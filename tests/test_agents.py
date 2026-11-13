import json
import unittest
from unittest import mock

try:
    import langchain_core  # noqa: F401
    _HAS_LANGCHAIN = True
except Exception:
    _HAS_LANGCHAIN = False


def _fake_llm(reply: str, captured: list):
    """A stand-in chat model: records the messages it receives and returns `reply`."""
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    def respond(messages):
        captured.append("\n".join(str(getattr(m, "content", m)) for m in messages))
        return AIMessage(content=reply)

    return RunnableLambda(respond)


IDOR_REPLY = json.dumps({
    "confidence_score": 2,
    "potential_business_impact": "Low",
    "testing_plan": ["Swap IDs between two accounts."],
    "affected_endpoints": None,
})


@unittest.skipUnless(_HAS_LANGCHAIN, "langchain is not installed in this environment")
class LogicAnalysisTests(unittest.TestCase):
    def test_returns_only_the_new_finding(self):
        from watchtower.agents import logic_analysis

        existing = [{"title": "Earlier finding", "severity": "Low"}]
        httpx_obs = {"target": "http://t", "tool": "httpx", "output": "200 OK /api/orders/1"}
        state = {"findings": existing, "observations": [httpx_obs], "latest_observations": [httpx_obs]}
        captured = []
        with mock.patch.object(logic_analysis, "get_llm", return_value=_fake_llm(IDOR_REPLY, captured)):
            result = logic_analysis.logic_analysis_node(state)

        # Regression: the node used to return existing findings plus the new one,
        # which the additive reducer duplicated.
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["title"], "IDOR Logic Analysis Plan")

    def test_runs_when_trigger_is_not_the_last_tool(self):
        from watchtower.agents import logic_analysis

        step = [
            {"target": "http://t", "tool": "httpx", "output": "200 OK"},
            {"target": "http://t", "tool": "wafw00f", "output": "No WAF detected"},
        ]
        captured = []
        with mock.patch.object(logic_analysis, "get_llm", return_value=_fake_llm(IDOR_REPLY, captured)):
            result = logic_analysis.logic_analysis_node(
                {"findings": [], "observations": step, "latest_observations": step}
            )
        self.assertEqual(len(captured), 1)
        self.assertIn("findings", result)

    def test_skips_when_no_trigger_in_latest_step(self):
        from watchtower.agents import logic_analysis

        step = [{"target": "http://t", "tool": "wafw00f", "output": "No WAF detected"}]
        with mock.patch.object(logic_analysis, "get_llm") as get_llm:
            result = logic_analysis.logic_analysis_node(
                {"findings": [], "observations": step, "latest_observations": step}
            )
        get_llm.assert_not_called()
        self.assertNotIn("findings", result)


@unittest.skipUnless(_HAS_LANGCHAIN, "langchain is not installed in this environment")
class AnalystTests(unittest.TestCase):
    def test_reviews_every_tool_in_the_step(self):
        from watchtower.agents import analyst

        step = [
            {"target": "http://t", "tool": "wafw00f", "output": "WAFW00F-OUTPUT"},
            {"target": "http://t", "tool": "httpx", "output": "HTTPX-OUTPUT"},
        ]
        captured = []
        with mock.patch.object(analyst, "get_llm", return_value=_fake_llm('{"findings": []}', captured)):
            result = analyst.analyst_node({"observations": step, "latest_observations": step})

        self.assertEqual(result, {"findings": []})
        prompt = captured[0]
        # Regression: only the last tool's output used to reach the analyst.
        for text in ("wafw00f", "WAFW00F-OUTPUT", "httpx", "HTTPX-OUTPUT"):
            self.assertIn(text, prompt)

    def test_falls_back_to_last_observation(self):
        from watchtower.agents import analyst

        obs = [{"target": "http://t", "tool": "nmap", "output": "NMAP-OUTPUT"}]
        captured = []
        with mock.patch.object(analyst, "get_llm", return_value=_fake_llm('{"findings": []}', captured)):
            analyst.analyst_node({"observations": obs})
        self.assertIn("NMAP-OUTPUT", captured[0])


@unittest.skipUnless(_HAS_LANGCHAIN, "langchain is not installed in this environment")
class PlannerTests(unittest.TestCase):
    PLAN = json.dumps({"current_plan": "recon", "next_step": "finish", "is_finished": True})

    def test_prompt_includes_target_and_type(self):
        from watchtower.agents import planner

        captured = []
        with mock.patch.object(planner, "get_llm", return_value=_fake_llm(self.PLAN, captured)):
            planner.planner_node({"scope_targets": ["http://127.0.0.1:8088"], "available_tools": ["nmap"]})
        prompt = captured[0]
        self.assertIn("http://127.0.0.1:8088", prompt)
        self.assertIn("127.0.0.1 (IP address)", prompt)

    def test_hostname_target_type(self):
        from watchtower.agents import planner

        captured = []
        with mock.patch.object(planner, "get_llm", return_value=_fake_llm(self.PLAN, captured)):
            planner.planner_node({"scope_targets": ["https://example.com/app"], "available_tools": []})
        self.assertIn("example.com (hostname)", captured[0])

    def test_llm_setup_error_ends_plan_cleanly(self):
        from watchtower.agents import planner

        with mock.patch.object(planner, "get_llm", side_effect=ValueError("bad provider config")):
            result = planner.planner_node({"scope_targets": ["http://t"], "available_tools": []})
        self.assertTrue(result["is_finished"])
        self.assertEqual(result["next_step"], "finish")
        self.assertIn("bad provider config", result["current_plan"])


if __name__ == "__main__":
    unittest.main()
