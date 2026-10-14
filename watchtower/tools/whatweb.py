from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import normalize_url

def run(target: str, **kwargs) -> str:
    command = ["whatweb", "-a", "3", normalize_url(target)]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
