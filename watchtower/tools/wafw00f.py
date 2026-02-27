from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["wafw00f", "-a", target]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
