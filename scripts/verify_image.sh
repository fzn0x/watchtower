#!/usr/bin/env bash
# Verify a built Watchtower Docker image on Linux.
#
# usage: scripts/verify_image.sh [image]   (default: watchtower:ci)
#
# Checks that Watchtower starts, that ProjectDiscovery's httpx scanner is
# installed and resolved ahead of Python's httpx client, that the scanner can
# probe a local server through Watchtower's wrapper, and that every supported
# tool is installed.
set -euo pipefail

IMAGE="${1:-watchtower:ci}"

echo "== Watchtower starts"
docker run --rm "$IMAGE" python -m watchtower.main --version

echo "== httpx: the scanner resolves ahead of Python's httpx client"
docker run --rm -i "$IMAGE" python - <<'PY'
import shutil
from watchtower.core.binaries import find_pd_httpx, is_python_httpx_cli

on_path = shutil.which("httpx")
print("httpx on PATH:     ", on_path, "(Python client)" if on_path and is_python_httpx_cli(on_path) else "")
print("pd-httpx on PATH:  ", shutil.which("pd-httpx"))
scanner = find_pd_httpx()
print("scanner resolved:  ", scanner)
assert scanner, "ProjectDiscovery httpx scanner was not found in the image"
assert not is_python_httpx_cli(scanner), "resolved httpx is Python's client, not the scanner"
PY

echo "== httpx: Watchtower's wrapper probes a local server"
docker run --rm -i "$IMAGE" sh -s <<'SH'
set -e
mkdir -p /tmp/site
printf '<html><head><title>Watchtower CI probe</title></head><body>ok</body></html>' > /tmp/site/index.html
python -m http.server 8000 --bind 127.0.0.1 --directory /tmp/site >/dev/null 2>&1 &
python - <<'PY'
import time, urllib.request
from watchtower.tools import httpx

for _ in range(50):
    try:
        urllib.request.urlopen("http://127.0.0.1:8000", timeout=1)
        break
    except OSError:
        time.sleep(0.2)
out = httpx.run("http://127.0.0.1:8000")
print(out)
assert "200" in out and "Watchtower CI probe" in out, "scanner did not report the status and title"
PY
SH

echo "== Every supported tool is installed"
docker run --rm -i "$IMAGE" python - <<'PY'
from watchtower.core.binaries import split_installed
from watchtower.tools import ALL_TOOLS

installed, missing = split_installed(ALL_TOOLS)
print(f"installed ({len(installed)}/{len(ALL_TOOLS)}):", ", ".join(installed))
print("missing:", ", ".join(missing) or "none")
assert not missing, f"tools missing from the image: {', '.join(missing)}"
PY

echo "== Image verified"
