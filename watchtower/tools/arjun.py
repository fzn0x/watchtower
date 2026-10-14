from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import normalize_url

def run(target: str, **kwargs) -> str:
    command = ["arjun", "-u", normalize_url(target), "-t", "10", "-T", "5"]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
