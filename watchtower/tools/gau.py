from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import extract_hostname, is_ip_address


def run(target: str, **kwargs) -> str:
    host = extract_hostname(target)
    if is_ip_address(host):
        return "gau skipped: the target is an IP address; gau looks up archived URLs by domain."
    # Historical URLs for this host only (no --subs, to stay in scope), without
    # static assets that never carry parameters.
    command = [
        "gau", host,
        "--providers", "wayback,commoncrawl,otx,urlscan",
        "--threads", "5",
        "--timeout", "30",
        "--blacklist", "ttf,woff,woff2,svg,png,jpg,jpeg,gif,ico,css",
    ]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
