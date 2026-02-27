from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["subfinder", "-d", target, "-silent", "-all"]
    return run_cli_tool(command)
