from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import extract_hostname

def run(target: str, **kwargs) -> str:
    command = ["subfinder", "-d", extract_hostname(target), "-silent", "-all"]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
