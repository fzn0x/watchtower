import importlib
from watchtower.core.state import AgentState

def worker_node(state: AgentState) -> dict:
    next_step = state.get("next_step", "finish")
    available_tools = state.get("available_tools", [])
    
    if next_step == "finish" or next_step not in available_tools:
        return {"observations": []}
    
    target = state["scope_targets"][0]
    
    try:
        tool_module = importlib.import_module(f"watchtower.tools.{next_step}")
        raw_output = tool_module.run(target)
    except Exception as e:
        raw_output = f"Error: {e}"
        
    observation = {
        "target": target,
        "tool": next_step,
        "output": raw_output
    }
    return {"observations": [observation]}
