import json
import logging
from pydantic import BaseModel, Field
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from watchtower.core.state import AgentState, latest_step_observations
from watchtower.agents.planner import get_llm

class Finding(BaseModel):
    title: str = Field(description="A concise title for the discovered vulnerability or configuration issue.")
    severity: str = Field(description="Critical, High, Medium, Low, or Info.")
    description: str = Field(description="Detailed explanation of the issue.")
    evidence: str = Field(description="The exact snippet of text from the output proving the finding.")

class AnalystOutput(BaseModel):
    findings: List[Finding] = Field(description="A list of confirmed, legitimate findings. Omit false positives.")

def _format_tool_outputs(observations: list) -> str:
    sections = []
    for obs in observations:
        sections.append(
            f"[Tool: {obs.get('tool', 'Unknown')}]\n"
            f"{obs.get('output', 'None')}"
        )
    return "\n\n".join(sections)


def analyst_node(state: AgentState) -> dict:
    latest = latest_step_observations(state)
    if not latest:
        return {"findings": []}

    target = latest[0].get("target", "Unknown")
    tools = ", ".join(obs.get("tool", "Unknown") for obs in latest)

    parser = PydanticOutputParser(pydantic_object=AnalystOutput)

    prompt = f"""
You are an expert Security Analyst. Review the raw output from the automated security tools.
Your goal is to identify genuine security vulnerabilities or interesting misconfigurations.

Tool Execution Details:
Target: {target}
Tools Used: {tools}

Raw Output (one section per tool):
{_format_tool_outputs(latest)}

Review every tool's output. Extract any true findings as structured data. If the output contains only normal behavior or tool errors, return an empty list.
{parser.get_format_instructions()}
"""
    
    try:
        llm = get_llm()
        chain = llm | parser
        result = chain.invoke([HumanMessage(content=prompt)])
        new_findings = [f.model_dump() for f in result.findings]
        return {"findings": new_findings}
    except Exception as e:
        logging.error(f"Analyst execution error: {e}")
        return {"findings": []}
