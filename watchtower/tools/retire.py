from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import normalize_url

def run(target: str, **kwargs) -> str:
    command = ["retire", "--site", normalize_url(target), "--outputformat", "text"]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
