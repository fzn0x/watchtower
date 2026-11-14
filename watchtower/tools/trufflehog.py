from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import looks_like_git_repo


def run(target: str, **kwargs) -> str:
    if not looks_like_git_repo(target):
        return (
            "trufflehog skipped: the target is not a git repository URL. trufflehog scans "
            "git history, not live web or network targets. Point it at a repository "
            "(e.g. https://github.com/owner/repo) to use it."
        )
    # Secrets confirmed live (verified) or whose check errored (unknown).
    command = [
        "trufflehog", "git", target.strip(),
        "--results=verified,unknown",
        "--json",
        "--no-update",
    ]
    return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
