from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["masscan", "-p1-65535", "--rate", "1000", target]
    return run_cli_tool(command)
