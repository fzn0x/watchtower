from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import extract_hostname


def run(target: str, **kwargs) -> str:
    # Fast port discovery on the top 1000 ports (CONNECT scan, the default,
    # so it does not need root).
    command = [
        "naabu", "-host", extract_hostname(target),
        "-top-ports", "1000",
        "-silent", "-nc",
    ]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
