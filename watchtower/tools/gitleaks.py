import shutil
import subprocess
import tempfile
import urllib.parse

from watchtower.tools.runner import run_cli_tool

_GIT_HOSTS = {"github.com", "gitlab.com", "bitbucket.org"}


def _looks_like_git_repo(target: str) -> bool:
    """True if the target looks like a cloneable git repository URL.

    gitleaks scans git history / a filesystem, not a live web endpoint, so it
    only makes sense against a repository. A plain site or IP is not one.
    """
    if not target:
        return False

    candidate = target.strip()
    if candidate.endswith(".git"):
        return True

    if "://" not in candidate:
        candidate = "//" + candidate
    parsed = urllib.parse.urlparse(candidate)
    host = (parsed.hostname or "").lower()
    path_parts = [p for p in parsed.path.split("/") if p]

    # A known forge with an owner/repo path (e.g. github.com/owner/repo).
    return host in _GIT_HOSTS and len(path_parts) >= 2


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
