from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["xsstrike", "-u", target]
    return run_cli_tool(command)
