from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["sqlmap", "-u", target, "--batch", "--random-agent", "--level=2", "--risk=2", "--crawl=2"]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
