from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["gitleaks", "detect", "-v"]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
