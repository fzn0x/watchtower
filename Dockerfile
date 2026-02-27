FROM python:3.11-slim

# Install system dependencies and security tools
RUN apt-get update && apt-get install -y \
    nmap \
    masscan \
    curl \
    wget \
    git \
    make \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Install Nuclei (example of installing a Go-based tool from binaries)
# Note: In a complete production image, you would add more tools (httpx, subfinder, etc.)
RUN wget https://github.com/projectdiscovery/nuclei/releases/download/v3.0.0/nuclei_3.0.0_linux_amd64.zip \
    && apt-get update && apt-get install -y unzip \
    && unzip nuclei_3.0.0_linux_amd64.zip \
    && mv nuclei /usr/local/bin/ \
    && rm nuclei_3.0.0_linux_amd64.zip

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the framework
CMD ["python", "-m", "watchtower.main"]
