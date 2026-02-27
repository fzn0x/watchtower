import os
import json
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from watchtower.core.state import AgentState

class PlannerOutput(BaseModel):
    current_plan: str = Field(description="The updated strategy based on findings.")
    next_step: str = Field(description="The exact name of the next tool to run (e.g. 'nmap', 'httpx') or 'finish'.")
    is_finished: bool = Field(description="True if the pentest is complete, False otherwise.")

def get_llm():
    custom_provider = os.getenv("WATCHTOWER_PROVIDER")
    custom_model = os.getenv("WATCHTOWER_MODEL", "gpt-4-turbo")
    apikey_env_name = os.getenv("WATCHTOWER_APIKEY_NAME")
    
    if custom_provider:
        api_key = os.getenv(apikey_env_name) if apikey_env_name else None
        provider = custom_provider.lower()
        
        if provider.startswith("http"):
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=custom_model, 
                temperature=0, 
                api_key=api_key, 
                base_url=provider,
            )
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=custom_model, temperature=0, api_key=api_key)
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model_name=custom_model, temperature=0, api_key=api_key)
        elif provider == "openrouter":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=custom_model, temperature=0, api_key=api_key, base_url="https://openrouter.ai/api/v1")
        elif provider == "litellm":
            from langchain_community.chat_models import ChatLiteLLM
            return ChatLiteLLM(model=custom_model, temperature=0, api_key=api_key)
        else:
            try:
                from langchain.chat_models import init_chat_model
                return init_chat_model(custom_model, model_provider=provider, temperature=0, api_key=api_key)
            except Exception:
                from langchain_community.chat_models import ChatLiteLLM
                return ChatLiteLLM(model=custom_model, temperature=0, api_key=api_key)

    if os.getenv("OPENROUTER_API_KEY"):
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("OPENROUTER_MODEL_NAME", "anthropic/claude-3-opus")
        return ChatOpenAI(
            model=model_name, 
            temperature=0, 
            api_key=os.getenv("OPENROUTER_API_KEY"), 
            base_url="https://openrouter.ai/api/v1"
        )
    elif os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo")
        return ChatOpenAI(model=model_name, temperature=0)
    elif os.getenv("GEMINI_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
        return ChatGoogleGenerativeAI(model=model_name, temperature=0)
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

def planner_node(state: AgentState) -> dict:
    findings = state.get("findings", [])
    observations = state.get("observations", [])
    
    available_tools = state.get("available_tools", [])
    tool_list_str = "\n".join([f"- `{t}`" for t in available_tools])
    
    parser = PydanticOutputParser(pydantic_object=PlannerOutput)
    
    prompt = f"""
You are an expert autonomous pentesting planner.
Your goal is to strategize the next sequence of actions based on current findings.

Available tools you can specify in next_step (Do NOT hallucinate tools outside this list!!):
{tool_list_str}
- `finish` (If no further testing is needed)

Current Findings:
{json.dumps(findings, indent=2)}

Recent Observations:
{json.dumps(observations[-3:] if observations else [], indent=2)}

Decide the next logical step. Do not repeat tools unnecessarily.
{parser.get_format_instructions()}
"""
    llm = get_llm()
    try:
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
