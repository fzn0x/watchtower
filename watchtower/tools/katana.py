from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import normalize_url


def run(target: str, **kwargs) -> str:
    # Crawl the site for endpoints, including ones referenced from JavaScript.
    command = [
        "katana", "-u", normalize_url(target),
        "-silent", "-nc",       # plain, uncolored output
        "-d", "2",              # crawl depth
        "-jc",                  # parse endpoints from JavaScript files
        "-timeout", "10",       # seconds per request
        "-rl", "50",            # requests per second
    ]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
