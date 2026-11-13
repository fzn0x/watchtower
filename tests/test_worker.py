import sys
import threading
import types
import unittest
from unittest import mock

# The worker only pulls langchain via the AgentState type hint in core.state.
# Stub that module when langchain is absent so the test runs anywhere.
try:
    import langchain_core  # noqa: F401
except Exception:
    _stub = types.ModuleType("watchtower.core.state")
    _stub.AgentState = dict
    sys.modules.setdefault("watchtower.core.state", _stub)

from watchtower.agents import worker


def _fake_module(name, run_fn):
    mod = types.ModuleType(name)
    mod.run = run_fn
    return mod


class WorkerTests(unittest.TestCase):
    def test_runs_tools_concurrently_and_preserves_order(self):
        tools = ["nmap", "httpx", "whatweb"]
        # A barrier only clears if all tools run at the same time. Sequential
        # execution would make barrier.wait() time out and break.
        barrier = threading.Barrier(len(tools), timeout=5)

        def run_fn(target, auth_metadata=None):
            barrier.wait()
            return f"ok:{target}"

        def fake_import(path):
            return _fake_module(path, run_fn)

        with mock.patch("watchtower.agents.worker.importlib.import_module", side_effect=fake_import):
            result = worker.worker_node({
                "next_step": tools,
                "available_tools": tools,
                "auth_metadata": {},
                "scope_targets": ["example.com"],
            })

        obs = result["observations"]
        self.assertEqual([o["tool"] for o in obs], tools)
        self.assertTrue(all(o["output"] == "ok:example.com" for o in obs))
        # The whole step is published so the analyst can review every tool.
        self.assertEqual(result["latest_observations"], obs)

    def test_skips_unavailable_tools(self):
        def fake_import(path):
            return _fake_module(path, lambda target, auth_metadata=None: "ran")

        with mock.patch("watchtower.agents.worker.importlib.import_module", side_effect=fake_import):
            result = worker.worker_node({
                "next_step": ["nmap", "notallowed"],
                "available_tools": ["nmap"],
                "auth_metadata": {},
                "scope_targets": ["example.com"],
            })

        self.assertEqual([o["tool"] for o in result["observations"]], ["nmap"])

    def test_captures_tool_errors(self):
        def boom(target, auth_metadata=None):
            raise RuntimeError("kaboom")

        with mock.patch("watchtower.agents.worker.importlib.import_module",
                        side_effect=lambda path: _fake_module(path, boom)):
            result = worker.worker_node({
                "next_step": "nmap",
                "available_tools": ["nmap"],
                "auth_metadata": {},
                "scope_targets": ["example.com"],
            })

        self.assertEqual(len(result["observations"]), 1)
        self.assertIn("kaboom", result["observations"][0]["output"])

    def test_finish_returns_no_observations(self):
        result = worker.worker_node({
            "next_step": "finish",
            "available_tools": ["nmap"],
            "auth_metadata": {},
            "scope_targets": ["example.com"],
        })
        self.assertEqual(result, {"observations": [], "latest_observations": []})


if __name__ == "__main__":
    unittest.main()
