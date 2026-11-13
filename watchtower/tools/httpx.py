from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import normalize_url
from watchtower.core.binaries import find_pd_httpx


def run(target: str, **kwargs) -> str:
    binary = find_pd_httpx()
    if not binary:
        return (
            "httpx skipped: ProjectDiscovery httpx was not found. Any 'httpx' on PATH is "
            "Python's HTTP client, not the scanner. Install it with install_tools.sh or "
            "set WATCHTOWER_HTTPX_BIN to its path."
        )
    command = [
        binary, "-u", normalize_url(target),
        "-silent", "-nc",                          # plain, uncolored output
        "-sc", "-title", "-td", "-server", "-cl",  # status, title, tech, server, length
        "-fr",                                     # follow redirects
    ]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
