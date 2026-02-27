from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["whatweb", "-a", "3", target]
    return run_cli_tool(command)
