from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import extract_hostname

def run(target: str, **kwargs) -> str:
    command = ["masscan", "-p1-65535", "--rate", "1000", extract_hostname(target)]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
