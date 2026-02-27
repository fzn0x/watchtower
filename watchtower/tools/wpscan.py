from watchtower.tools.runner import run_cli_tool

def run(target: str, **kwargs) -> str:
    command = ["wpscan", "--url", target, "--no-banner", "--random-user-agent", "--enumerate", "vp,vt,tt,cb,dbe,u,m"]
    return run_cli_tool(command)
