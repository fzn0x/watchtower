#!/bin/bash
# ============================================================
# Security Tools Installer
# Installs: nmap, masscan, whatweb, wafw00f, subfinder, amass,
#           dnsrecon, nuclei, nikto, sqlmap, wpscan, testssl,
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
    *)                  warn "Unknown OS: $OS — skipping apt install of $*" ;;
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
go_install() {
  local name=$1
  local pkg=$2
  log "Installing $name..."
  GOPATH=$HOME/go go install "$pkg" 2>&1 | tail -3 || warn "Failed to install $name"
  local bin
  bin=$(basename "${pkg%%@*}")
  [[ -f "$HOME/go/bin/$bin" ]] && ln -sf "$HOME/go/bin/$bin" /usr/local/bin/"$bin" || true
}

# ── Helper: install GitHub release binary ─────────────────
github_release_install() {
  local name=$1 repo=$2 asset_pattern=$3 binary_name=$4
  log "Installing $name from GitHub releases..."
  local url
  url=$(curl -s "https://api.github.com/repos/${repo}/releases/latest" \
        | grep "browser_download_url" \
        | grep -E "$asset_pattern" \
        | head -1 \
        | cut -d '"' -f4)
  if [[ -z "$url" ]]; then
    warn "Could not find release asset for $name"
    return
  fi
  local tmp="/tmp/${name}_release"
  mkdir -p "$tmp"
  wget -q "$url" -O "$tmp/asset"
  if file "$tmp/asset" | grep -q "Zip\|zip"; then
    unzip -o "$tmp/asset" -d "$tmp/extracted"
  elif file "$tmp/asset" | grep -q "gzip\|tar"; then
    tar -xzf "$tmp/asset" -C "$tmp/extracted" 2>/dev/null || tar -xf "$tmp/asset" -C "$tmp/extracted" 2>/dev/null || true
  else
    cp "$tmp/asset" "$tmp/extracted/$binary_name"
  fi
  local bin
  bin=$(find "$tmp/extracted" -name "$binary_name" -type f 2>/dev/null | head -1)
  if [[ -z "$bin" ]]; then
    # maybe the asset itself is the binary
    bin=$(find "$tmp" -maxdepth 1 -name "asset")
  fi
  [[ -n "$bin" ]] && install -m 755 "$bin" /usr/local/bin/"$binary_name" && log "$name installed."
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
gem install wpscan 2>/dev/null || warn "wpscan gem install failed — ensure ruby-dev is present"

# ════════════════════════════════════════════════════════════
# 12. testssl.sh
# ════════════════════════════════════════════════════════════
log "Installing testssl.sh..."
cd /opt/security-tools
git clone --depth 1 https://github.com/drwetter/testssl.sh.git 2>/dev/null || true
ln -sf /opt/security-tools/testssl.sh/testssl.sh /usr/local/bin/testssl

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
go_install gitleaks github.com/gitleaks/gitleaks/v8@latest

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
KITE_REPO="assetnote/kiterunner"
KITE_ASSET="kiterunner_linux_amd64.tar.gz"
github_release_install kiterunner "$KITE_REPO" "$KITE_ASSET" "kr"

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

TOOLS=(nmap masscan whatweb wafw00f subfinder amass dnsrecon nuclei \
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