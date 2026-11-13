import shutil
import subprocess
import tempfile

from watchtower.tools.runner import run_cli_tool
from watchtower.core.targets import looks_like_git_repo as _looks_like_git_repo


def run(target: str, **kwargs) -> str:
    """Scan a git repository for leaked secrets.

    If the target is a repository URL it is cloned to a temporary directory and
    scanned there. Otherwise gitleaks is skipped with a clear message, since it
    cannot do anything useful with a web or network target.
    """
    if not _looks_like_git_repo(target):
        return (
            "gitleaks skipped: the target is not a git repository URL. "
            "gitleaks scans git history, not live web or network targets. "
            "Point it at a repository (e.g. https://github.com/owner/repo) to use it."
        )

    tmp_dir = tempfile.mkdtemp(prefix="watchtower-gitleaks-")
    try:
        clone = subprocess.run(
            ["git", "clone", "--depth", "1", target.strip(), tmp_dir],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if clone.returncode != 0:
            return f"gitleaks skipped: failed to clone {target}.\n{clone.stderr}"

        command = ["gitleaks", "detect", "--source", tmp_dir, "-v"]
        return run_cli_tool(command, auth_metadata=kwargs.get("auth_metadata"))
    except Exception as e:
        return f"Error executing gitleaks: {e}"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
