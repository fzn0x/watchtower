from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["httpx", target, "-m", "GET", "--follow-redirects"]
    return run_cli_tool(command)
