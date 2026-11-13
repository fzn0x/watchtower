import importlib
from concurrent.futures import ThreadPoolExecutor

from watchtower.core.state import AgentState

# Cap concurrent tool processes so a single step does not spawn an unbounded
# number of heavy scanners at once.
MAX_CONCURRENCY = 5


def _run_tool(tool_name: str, target: str, auth_metadata: dict) -> dict:
    try:
        tool_module = importlib.import_module(f"watchtower.tools.{tool_name}")
        raw_output = tool_module.run(target, auth_metadata=auth_metadata)
    except Exception as e:
        raw_output = f"Error: {e}"

    return {"target": target, "tool": tool_name, "output": raw_output}


def worker_node(state: AgentState) -> dict:
    next_step = state.get("next_step", "finish")
    available_tools = state.get("available_tools", [])
    auth_metadata = state.get("auth_metadata", {})

    # Handle single string or list of tools
    tools_to_run = [next_step] if isinstance(next_step, str) else next_step

    if "finish" in tools_to_run or not tools_to_run:
        return {"observations": []}

    target = state["scope_targets"][0]
    runnable = [t for t in tools_to_run if t in available_tools]

    if not runnable:
        return {"observations": []}

    if len(runnable) == 1:
        return {"observations": [_run_tool(runnable[0], target, auth_metadata)]}

    # Each tool is a blocking subprocess, so threads give real concurrency.
    # executor.map preserves input order, keeping observations deterministic.
    max_workers = min(len(runnable), MAX_CONCURRENCY)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        observations = list(
            executor.map(lambda t: _run_tool(t, target, auth_metadata), runnable)
        )

    return {"observations": observations}
