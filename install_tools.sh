#!/bin/bash
# ============================================================
# Security Tools Installer
# Installs: nmap, masscan, whatweb, wafw00f, httpx, subfinder,
#           amass, dnsrecon, nuclei, nikto, sqlmap, wpscan, testssl,
#           sslyze, gobuster, ffuf, arjun, xsstrike, gitleaks,
#           cmseek, retire, dalfox, kiterunner
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[-]${NC} $1"; }

INSTALL_DIR="/opt/security-tools"
mkdir -p "$INSTALL_DIR"

# ── Detect OS ──────────────────────────────────────────────
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS=$ID
else
  OS=$(uname -s | tr '[:upper:]' '[:lower:]')
fi

# ── Package manager setup ──────────────────────────────────
install_pkg() {
  case $OS in
    ubuntu|debian|kali) apt-get install -y "$@" ;;
    fedora|rhel|centos) dnf install -y "$@" ;;
    arch|manjaro)       pacman -Sy --noconfirm "$@" ;;
    *)                  warn "Unknown OS: $OS, skipping apt install of $*" ;;
  esac
}

log "Updating package lists..."
case $OS in
  ubuntu|debian|kali) apt-get update -qq ;;
  fedora|rhel|centos) dnf check-update -q || true ;;
  arch|manjaro)       pacman -Sy --noconfirm ;;
esac

# ── System dependencies ────────────────────────────────────
log "Installing system dependencies..."
install_pkg curl wget git ruby ruby-dev build-essential \
            libssl-dev libffi-dev python3 python3-pip python3-venv \
            libpcap-dev unzip tar 2>/dev/null || true

# ── Go (needed for several tools) ─────────────────────────
install_go() {
  if command -v go &>/dev/null; then
    log "Go already installed: $(go version)"
    return
  fi
  log "Installing Go..."
  GO_VERSION="1.22.2"
  ARCH=$(uname -m)
  case $ARCH in
    x86_64)  GOARCH="amd64" ;;
    aarch64) GOARCH="arm64" ;;
    *)       GOARCH="amd64" ;;
  esac
  wget -q "https://go.dev/dl/go${GO_VERSION}.linux-${GOARCH}.tar.gz" -O /tmp/go.tar.gz
  rm -rf /usr/local/go
  tar -C /usr/local -xzf /tmp/go.tar.gz
  rm /tmp/go.tar.gz
  export PATH=$PATH:/usr/local/go/bin
  echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> /etc/profile.d/go.sh
  log "Go $(go version) installed."
}

install_go
export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin

# ── Helper: install Go binary ──────────────────────────────
# Reports a failed build instead of hiding it, then links the binary into
# /usr/local/bin. The binary is named after the package's last path element,
# skipping a trailing "/..." and a major-version suffix such as "/v8".
go_install() {
  local name=$1
  local pkg=$2
  log "Installing $name..."
  local log_file="/tmp/go_install_${name}.log"
  if ! GOPATH=$HOME/go go install "$pkg" >"$log_file" 2>&1; then
    tail -5 "$log_file"
    warn "Failed to install $name"
    return 0
  fi
  local path="${pkg%%@*}"
  path="${path%/...}"
  local bin
  bin=$(basename "$path")
  if [[ "$bin" =~ ^v[0-9]+$ ]]; then
    bin=$(basename "$(dirname "$path")")
  fi
  if [[ -f "$HOME/go/bin/$bin" ]]; then
    ln -sf "$HOME/go/bin/$bin" /usr/local/bin/"$bin"
  else
    warn "$name built, but $HOME/go/bin/$bin was not found"
  fi
}

# ── Helper: install GitHub release binary ─────────────────
# Installs a binary from the latest release asset whose name matches
# asset_regex. When the release publishes a checksums.txt, the download is
# verified against it and not installed on a mismatch.
github_release_install() {
  local name=$1 repo=$2 asset_regex=$3 binary_name=$4
  log "Installing $name from GitHub releases..."
  local release urls url sums_url
  if ! release=$(curl -fsSL "https://api.github.com/repos/${repo}/releases/latest"); then
    warn "Could not query releases for $name"
    return 0
  fi
  urls=$(printf '%s' "$release" | grep -o '"browser_download_url": *"[^"]*"' | cut -d '"' -f4)
  url=$(printf '%s\n' "$urls" | grep -E "$asset_regex" | head -1)
  sums_url=$(printf '%s\n' "$urls" | grep -E 'checksums\.txt$' | head -1)
  if [[ -z "$url" ]]; then
    warn "Could not find release asset for $name"
    return 0
  fi
  local tmp asset
  tmp=$(mktemp -d)
  asset="$tmp/$(basename "$url")"
  if ! wget -q "$url" -O "$asset"; then
    warn "Download failed for $name"
    rm -rf "$tmp"
    return 0
  fi
  if [[ -n "$sums_url" ]]; then
    if wget -q "$sums_url" -O "$tmp/checksums.txt" \
       && (cd "$tmp" && grep " $(basename "$asset")\$" checksums.txt | sha256sum -c - >/dev/null); then
      log "$name checksum verified."
    else
      warn "Checksum verification failed for $name; not installing it."
      rm -rf "$tmp"
      return 0
    fi
  fi
  mkdir -p "$tmp/extracted"
  case "$asset" in
    *.zip)          unzip -oq "$asset" -d "$tmp/extracted" || true ;;
    *.tar.gz|*.tgz) tar -xzf "$asset" -C "$tmp/extracted" || true ;;
    *)              cp "$asset" "$tmp/extracted/$binary_name" ;;
  esac
  local bin
  bin=$(find "$tmp/extracted" -type f -name "$binary_name" | head -1)
  if [[ -n "$bin" ]]; then
    install -m 755 "$bin" /usr/local/bin/"$binary_name"
    log "$name installed."
  else
    warn "$binary_name was not found in the $name release asset"
  fi
  rm -rf "$tmp"
}

# ════════════════════════════════════════════════════════════
# 1. nmap
# ════════════════════════════════════════════════════════════
log "Installing nmap..."
install_pkg nmap

# ════════════════════════════════════════════════════════════
# 2. masscan
# ════════════════════════════════════════════════════════════
log "Installing masscan..."
install_pkg masscan 2>/dev/null || {
  cd /tmp && git clone --depth 1 https://github.com/robertdavidgraham/masscan.git
  cd masscan && make -j"$(nproc)" && install -m 755 bin/masscan /usr/local/bin/masscan
  cd / && rm -rf /tmp/masscan
}

# ════════════════════════════════════════════════════════════
# 3. whatweb
# ════════════════════════════════════════════════════════════
log "Installing whatweb..."
install_pkg whatweb 2>/dev/null || {
  gem install whatweb 2>/dev/null || {
    cd /opt/security-tools
    git clone --depth 1 https://github.com/urbanadventurer/WhatWeb.git whatweb
    ln -sf /opt/security-tools/whatweb/whatweb /usr/local/bin/whatweb
  }
}

# ════════════════════════════════════════════════════════════
# 4. wafw00f
# ════════════════════════════════════════════════════════════
log "Installing wafw00f..."
pip3 install wafw00f --break-system-packages 2>/dev/null || pip3 install wafw00f

# ════════════════════════════════════════════════════════════
# 4b. httpx (ProjectDiscovery HTTP prober)
# ════════════════════════════════════════════════════════════
# Also exposed as pd-httpx: Python's httpx package (installed later with
# Watchtower's requirements) ships its own `httpx` command that can replace
# /usr/local/bin/httpx, while pd-httpx stays pointed at the scanner.
go_install httpx github.com/projectdiscovery/httpx/cmd/httpx@latest
[[ -f "$HOME/go/bin/httpx" ]] && ln -sf "$HOME/go/bin/httpx" /usr/local/bin/pd-httpx || true

# ════════════════════════════════════════════════════════════
# 5. subfinder
# ════════════════════════════════════════════════════════════
go_install subfinder github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# ════════════════════════════════════════════════════════════
# 6. amass
# ════════════════════════════════════════════════════════════
go_install amass github.com/owasp-amass/amass/v4/...@master

# ════════════════════════════════════════════════════════════
# 7. dnsrecon
# ════════════════════════════════════════════════════════════
log "Installing dnsrecon..."
install_pkg dnsrecon 2>/dev/null || pip3 install dnsrecon --break-system-packages 2>/dev/null || {
  cd /opt/security-tools
  git clone --depth 1 https://github.com/darkoperator/dnsrecon.git
  pip3 install -r dnsrecon/requirements.txt --break-system-packages 2>/dev/null || true
  ln -sf /opt/security-tools/dnsrecon/dnsrecon.py /usr/local/bin/dnsrecon
}

# ════════════════════════════════════════════════════════════
# 8. nuclei
# ════════════════════════════════════════════════════════════
go_install nuclei github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# ════════════════════════════════════════════════════════════
# 9. nikto
# ════════════════════════════════════════════════════════════
log "Installing nikto..."
install_pkg nikto 2>/dev/null || {
  cd /opt/security-tools
  git clone --depth 1 https://github.com/sullo/nikto.git
  ln -sf /opt/security-tools/nikto/program/nikto.pl /usr/local/bin/nikto
}

# ════════════════════════════════════════════════════════════
# 10. sqlmap
# ════════════════════════════════════════════════════════════
log "Installing sqlmap..."
install_pkg sqlmap 2>/dev/null || {
  cd /opt/security-tools
  git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
  ln -sf /opt/security-tools/sqlmap/sqlmap.py /usr/local/bin/sqlmap
}

# ════════════════════════════════════════════════════════════
# 11. wpscan
# ════════════════════════════════════════════════════════════
log "Installing wpscan..."
gem install wpscan 2>/dev/null || warn "wpscan gem install failed, ensure ruby-dev is present"

# ════════════════════════════════════════════════════════════
# 12. testssl.sh
# ════════════════════════════════════════════════════════════
log "Installing testssl.sh..."
# The project moved from drwetter/testssl.sh (now an empty repository) to
# testssl/testssl.sh; the 3.2 branch is the stable release line.
cd /opt/security-tools
if [[ ! -f testssl.sh/testssl.sh ]]; then
  rm -rf testssl.sh
  git clone --depth 1 --branch 3.2 https://github.com/testssl/testssl.sh.git testssl.sh \
    || warn "testssl.sh clone failed"
fi
if [[ -f /opt/security-tools/testssl.sh/testssl.sh ]]; then
  ln -sf /opt/security-tools/testssl.sh/testssl.sh /usr/local/bin/testssl
else
  warn "testssl.sh was not installed"
fi

# ════════════════════════════════════════════════════════════
# 13. sslyze
# ════════════════════════════════════════════════════════════
log "Installing sslyze..."
pip3 install sslyze --break-system-packages 2>/dev/null || pip3 install sslyze

# ════════════════════════════════════════════════════════════
# 14. gobuster
# ════════════════════════════════════════════════════════════
go_install gobuster github.com/OJ/gobuster/v3@latest

# ════════════════════════════════════════════════════════════
# 15. ffuf
# ════════════════════════════════════════════════════════════
go_install ffuf github.com/ffuf/ffuf/v2@latest

# ════════════════════════════════════════════════════════════
# 16. arjun
# ════════════════════════════════════════════════════════════
log "Installing arjun..."
pip3 install arjun --break-system-packages 2>/dev/null || pip3 install arjun

# ════════════════════════════════════════════════════════════
# 17. xsstrike
# ════════════════════════════════════════════════════════════
log "Installing xsstrike..."
cd /opt/security-tools
git clone --depth 1 https://github.com/s0md3v/XSStrike.git xsstrike 2>/dev/null || true
pip3 install -r xsstrike/requirements.txt --break-system-packages 2>/dev/null || true
cat > /usr/local/bin/xsstrike << 'EOF'
#!/bin/bash
python3 /opt/security-tools/xsstrike/xsstrike.py "$@"
EOF
chmod +x /usr/local/bin/xsstrike

# ════════════════════════════════════════════════════════════
# 18. gitleaks
# ════════════════════════════════════════════════════════════
# The module still declares its original path, so install it under that name.
go_install gitleaks github.com/zricethezav/gitleaks/v8@latest

# ════════════════════════════════════════════════════════════
# 19. cmseek
# ════════════════════════════════════════════════════════════
log "Installing cmseek..."
cd /opt/security-tools
git clone --depth 1 https://github.com/Tuhinshubhra/CMSeeK.git cmseek 2>/dev/null || true
pip3 install -r cmseek/requirements.txt --break-system-packages 2>/dev/null || true
cat > /usr/local/bin/cmseek << 'EOF'
#!/bin/bash
python3 /opt/security-tools/cmseek/cmseek.py "$@"
EOF
chmod +x /usr/local/bin/cmseek

# ════════════════════════════════════════════════════════════
# 20. retire.js (retire)
# ════════════════════════════════════════════════════════════
log "Installing retire.js..."
if command -v npm &>/dev/null; then
  npm install -g retire 2>/dev/null || warn "retire npm install failed"
else
  install_pkg nodejs npm 2>/dev/null && npm install -g retire 2>/dev/null || warn "npm not available for retire"
fi

# ════════════════════════════════════════════════════════════
# 21. dalfox
# ════════════════════════════════════════════════════════════
go_install dalfox github.com/hahwul/dalfox/v2@latest

# ════════════════════════════════════════════════════════════
# 22. kiterunner
# ════════════════════════════════════════════════════════════
log "Installing kiterunner..."
# Release assets are versioned, e.g. kiterunner_1.0.2_linux_amd64.tar.gz.
case "$(uname -m)" in
  aarch64|arm64) KITE_ARCH="arm64" ;;
  *)             KITE_ARCH="amd64" ;;
esac
github_release_install kiterunner "assetnote/kiterunner" "kiterunner_[0-9.]+_linux_${KITE_ARCH}\.tar\.gz$" "kr"

# ════════════════════════════════════════════════════════════
# Download nuclei templates
# ════════════════════════════════════════════════════════════
if command -v nuclei &>/dev/null; then
  log "Updating nuclei templates..."
  nuclei -update-templates 2>/dev/null || true
fi

# ════════════════════════════════════════════════════════════
# Verification summary
# ════════════════════════════════════════════════════════════
echo ""
echo "════════════════════════════════════════"
echo "         Installation Summary           "
echo "════════════════════════════════════════"

TOOLS=(nmap masscan whatweb wafw00f pd-httpx subfinder amass dnsrecon nuclei \
       nikto sqlmap wpscan testssl sslyze gobuster ffuf arjun xsstrike \
       gitleaks cmseek retire dalfox kr)

for t in "${TOOLS[@]}"; do
  if command -v "$t" &>/dev/null; then
    echo -e "  ${GREEN}✔${NC}  $t"
  else
    echo -e "  ${RED}✘${NC}  $t  (not found in PATH)"
  fi
done

echo ""
log "Done! You may need to run: source /etc/profile.d/go.sh"
log "Tools cloned to: $INSTALL_DIR"