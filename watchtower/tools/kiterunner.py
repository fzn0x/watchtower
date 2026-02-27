from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["kr", "scan", target, "-A=apiroutes-2202"]
    return run_cli_tool(command)
