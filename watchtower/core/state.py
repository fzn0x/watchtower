import operator
from typing import Annotated, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Represents the state of the LangGraph execution.
    """
    scope_targets: List[str]                  # Targets allowed to scan
    available_tools: List[str]                # Tools the user has explicitly permitted the LLM to use
    messages: Annotated[List[str], operator.add] 
    findings: Annotated[List[Dict[str, Any]], operator.add]  # Confirmed vulnerabilities
    observations: Annotated[List[Dict[str, Any]], operator.add] # Raw logs/tool results
    latest_observations: List[Dict[str, Any]] # Tool results from the most recent worker step (replaced each step)
    current_plan: str                         # The planner's current strategy
    next_step: str | List[str]                # The exact name of the next tool(s) to run
    auth_metadata: Dict[str, str]             # Authentication cookies/headers
    is_finished: bool                         # Whether the pentest is complete


def latest_step_observations(state) -> list:
    """Observations produced by the most recent worker step.

    Falls back to the last observation for states that predate
    `latest_observations`.
    """
    latest = state.get("latest_observations")
    if latest:
        return list(latest)
    observations = state.get("observations") or []
    return observations[-1:]
