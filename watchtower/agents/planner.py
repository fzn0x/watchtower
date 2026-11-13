import os
import json
import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from watchtower.core.state import AgentState
from watchtower.core.llm_config import read_llm_runtime, select_model, build_chat_kwargs, effort_notice

# get_llm runs on every agent step; only warn about a lowered effort once.
_effort_notices_logged = set()

class PlannerOutput(BaseModel):
    current_plan: str = Field(description="The updated strategy based on findings.")
    next_step: str | List[str] = Field(description="The exact name of the next tool(s) to run (e.g. 'nmap', 'httpx') or a list of tools for parallel recon/testing, or 'finish'.")
    is_finished: bool = Field(description="True if the pentest is complete, False otherwise.")

def get_llm():
    custom_provider = os.getenv("WATCHTOWER_PROVIDER")
    custom_model = os.getenv("WATCHTOWER_MODEL", "gpt-5.6")
    apikey_env_name = os.getenv("WATCHTOWER_APIKEY_NAME")
    rt = read_llm_runtime()

    def settings(family, configured_model):
        # Returns (model, kwargs) with flagship selection and reasoning applied.
        notice = effort_notice(family, rt["effort"], rt["flagship"])
        if notice and notice not in _effort_notices_logged:
            _effort_notices_logged.add(notice)
            logging.warning(notice)
        model = select_model(family, configured_model, rt["flagship"])
        kwargs = build_chat_kwargs(family, rt["effort"], rt["max_tokens"], rt["flagship"])
        return model, kwargs

    if custom_provider:
        api_key = os.getenv(apikey_env_name) if apikey_env_name else None
        provider = custom_provider.lower()

        if provider.startswith("http"):
            from langchain_openai import ChatOpenAI
            model, kwargs = settings("http", custom_model)
            return ChatOpenAI(model=model, api_key=api_key, base_url=custom_provider, **kwargs)
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            model, kwargs = settings("openai", custom_model)
            return ChatOpenAI(model=model, api_key=api_key, **kwargs)
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            model, kwargs = settings("anthropic", custom_model)
            return ChatAnthropic(model_name=model, api_key=api_key, **kwargs)
        elif provider == "openrouter":
            from langchain_openai import ChatOpenAI
            model, kwargs = settings("openrouter", custom_model)
            return ChatOpenAI(model=model, api_key=api_key, base_url="https://openrouter.ai/api/v1", **kwargs)
        elif provider == "litellm":
            from langchain_community.chat_models import ChatLiteLLM
            model, kwargs = settings("litellm", custom_model)
            return ChatLiteLLM(model=model, api_key=api_key, **kwargs)
        else:
            model, kwargs = settings("generic", custom_model)
            try:
                from langchain.chat_models import init_chat_model
                return init_chat_model(model, model_provider=provider, api_key=api_key, **kwargs)
            except Exception:
                from langchain_community.chat_models import ChatLiteLLM
                return ChatLiteLLM(model=model, api_key=api_key, **kwargs)

    if os.getenv("OPENROUTER_API_KEY"):
        from langchain_openai import ChatOpenAI
        model, kwargs = settings("openrouter", os.getenv("OPENROUTER_MODEL_NAME", "anthropic/claude-sonnet-5.5"))
        return ChatOpenAI(model=model, api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1", **kwargs)
    elif os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        model, kwargs = settings("openai", os.getenv("OPENAI_MODEL_NAME", "gpt-5.6"))
        return ChatOpenAI(model=model, **kwargs)
    elif os.getenv("GEMINI_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        model, kwargs = settings("gemini", os.getenv("GEMINI_MODEL_NAME", "gemini-3.8-flash"))
        return ChatGoogleGenerativeAI(model=model, **kwargs)
    else:
        class MockLLM:
            def with_structured_output(self, schema):
                class MockInvoker:
                    def invoke(self, msgs):
                        if schema.__name__ == "PlannerOutput":
                            return schema(current_plan="Mock fallback: Run nmap", next_step="finish", is_finished=True)
                        elif schema.__name__ == "AnalystOutput":
                            return schema(findings=[])
                        return schema()
                return MockInvoker()
        return MockLLM()

def _describe_target(state: AgentState) -> str:
    import ipaddress
    from watchtower.core.targets import extract_hostname

    targets = state.get("scope_targets") or []
    if not targets:
        return "Target: unknown"
    target = targets[0]
    host = extract_hostname(target)
    try:
        ipaddress.ip_address(host)
        target_type = "IP address"
    except ValueError:
        target_type = "hostname"
    return (
        f"Target (authorized, in scope): {target}\n"
        f"Host: {host} ({target_type})\n"
        "Choose tools that fit this target: for example, subdomain and DNS enumeration do not apply to a bare IP address."
    )


def planner_node(state: AgentState) -> dict:
    findings = state.get("findings", [])
    observations = state.get("observations", [])

    available_tools = state.get("available_tools", [])
    tool_list_str = "\n".join([f"- `{t}`" for t in available_tools])

    parser = PydanticOutputParser(pydantic_object=PlannerOutput)

    prompt = f"""
You are an expert autonomous pentesting planner.
Your goal is to strategize the next sequence of actions based on current findings.

{_describe_target(state)}

Available tools you can specify in next_step (Do NOT hallucinate tools outside this list!!):
{tool_list_str}
- `finish` (If no further testing is needed)

Current Findings:
{json.dumps(findings, indent=2)}

Recent Observations:
{json.dumps(observations[-3:] if observations else [], indent=2)}

Decide the next logical step. You can specify a single tool name (string) or a list of tool names for parallel execution (e.g., during the reconnaissance phase). Do not repeat tools unnecessarily. Ensure parallel tools don't conflict (e.g. avoid running multiple heavy scanners at once).
{parser.get_format_instructions()}
"""
    try:
        # Build the model inside the try so a provider setup error ends the plan
        # cleanly instead of crashing the run.
        llm = get_llm()
        # Instead of natively supported JSON outputs which fail on free OpenRouter models, we force JSON via text
        chain = llm | parser
        result = chain.invoke([HumanMessage(content=prompt)])
        return {
            "current_plan": result.current_plan,
            "next_step": result.next_step,
            "is_finished": result.is_finished
        }
    except Exception as e:
         return {"current_plan": f"Error: {str(e)}", "next_step": "finish", "is_finished": True}
