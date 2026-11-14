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

# Install every supported security tool through the bundled installer, so the
# image and a local install stay in sync (one source of truth). Only the
# installer is copied here, so this slow layer stays cached until the
# installer itself changes.
COPY install_tools.sh /tmp/install_tools.sh
RUN bash /tmp/install_tools.sh && rm -f /tmp/install_tools.sh

# Python dependencies for Watchtower itself, cached until requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the SQLite DB is writable.
RUN touch pentest_memory.db && chmod 666 pentest_memory.db

CMD ["python", "-m", "watchtower.main"]
