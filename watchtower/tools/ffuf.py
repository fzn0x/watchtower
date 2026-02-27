from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["ffuf", "-u", f"{target}/FUZZ", "-w", "wordlist.txt", "-t", "40", "-c"]
    return run_cli_tool(command)
