from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import extract_hostname, is_ip_address


def run(target: str, **kwargs) -> str:
    host = extract_hostname(target)
    if is_ip_address(host):
        return "dnsx skipped: the target is an IP address, so there are no DNS records to resolve for it."
    # dnsx reads hosts from stdin; resolve the common record types and show answers.
    command = [
        "dnsx", "-silent", "-nc",
        "-a", "-aaaa", "-cname", "-mx", "-ns", "-txt",
        "-resp",
    ]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"), input_text=host + "\n")
