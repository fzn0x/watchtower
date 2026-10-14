from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import normalize_url

def run(target: str, **kwargs) -> str:
    command = ["wpscan", "--url", normalize_url(target), "--no-banner", "--random-user-agent", "--enumerate", "vp,vt,tt,cb,dbe,u,m"]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
