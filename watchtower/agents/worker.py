import importlib
from watchtower.core.state import AgentState

def worker_node(state: AgentState) -> dict:
    next_step = state.get("next_step", "finish")
    available_tools = state.get("available_tools", [])
    auth_metadata = state.get("auth_metadata", {})
    
    # Handle single string or list of tools
    tools_to_run = [next_step] if isinstance(next_step, str) else next_step
    
    if "finish" in tools_to_run or not tools_to_run:
        return {"observations": []}
    
    target = state["scope_targets"][0]
    observations = []
    
    for tool_name in tools_to_run:
        if tool_name not in available_tools:
            continue
            
        try:
            tool_module = importlib.import_module(f"watchtower.tools.{tool_name}")
            # Pass auth_metadata to the tool module
            raw_output = tool_module.run(target, auth_metadata=auth_metadata)
        except Exception as e:
            raw_output = f"Error: {e}"
            
        observations.append({
            "target": target,
            "tool": tool_name,
            "output": raw_output
        })
        
    return {"observations": observations}
