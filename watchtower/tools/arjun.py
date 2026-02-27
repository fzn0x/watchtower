from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["arjun", "-u", target, "-t", "10", "-T", "5"]
    return run_cli_tool(command)
