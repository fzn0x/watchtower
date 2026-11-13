FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV GOPATH=/root/go
ENV PATH=$PATH:/usr/local/go/bin:/root/go/bin

WORKDIR /app

# Minimal utilities the installer itself needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    wget \
    git \
    file \
    ca-certificates \
    sudo \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Install every supported security tool through the bundled installer, so the
# image and a local install stay in sync (one source of truth). The installer
# detects the OS, installs system packages, Go, and the Go/Ruby/Python/git-based
# tools, and prints a summary of what resolved.
RUN chmod +x install_tools.sh && ./install_tools.sh

# Python dependencies for Watchtower itself.
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the SQLite DB is writable.
RUN touch pentest_memory.db && chmod 666 pentest_memory.db

CMD ["python", "-m", "watchtower.main"]
