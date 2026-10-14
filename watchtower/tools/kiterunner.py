from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import normalize_url

def run(target: str, **kwargs) -> str:
    command = ["kr", "scan", normalize_url(target), "-A=apiroutes-2202"]
    return run_cli_tool(command)
