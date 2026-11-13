from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import normalize_url
from watchtower.core.wordlists import default_wordlist

def run(target: str, **kwargs) -> str:
    command = ["ffuf", "-u", f"{normalize_url(target)}/FUZZ", "-w", default_wordlist(), "-t", "40", "-c"]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
