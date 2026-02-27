from langgraph.graph import StateGraph, END
from watchtower.core.state import AgentState
from watchtower.agents.planner import planner_node
from watchtower.agents.worker import worker_node
from watchtower.agents.analyst import analyst_node
from watchtower.agents.logic_analysis import logic_analysis_node

def create_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner", planner_node)
    graph.add_node("worker", worker_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("logic_analysis", logic_analysis_node)
    
    graph.set_entry_point("planner")
    
    def planner_router(state: AgentState):
        if state.get("is_finished"):
            return END
        return "worker"
    
    graph.add_conditional_edges("planner", planner_router)
    graph.add_edge("worker", "analyst")
    graph.add_edge("analyst", "logic_analysis")
    graph.add_edge("logic_analysis", "planner")
    return graph.compile()
