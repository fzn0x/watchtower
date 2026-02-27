FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nmap \
    masscan \
    curl \
    wget \
    git \
    make \
    dnsutils \
    unzip \
    ruby \
    ruby-dev \
    build-essential \
    libpcap-dev \
    golang \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set Go environment
ENV GOPATH=/go
ENV PATH=$PATH:/usr/local/go/bin:$GOPATH/bin

# Install Go-based tools
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/ffuf/ffuf/v2@latest && \
    go install -v github.com/OJ/gobuster/v3@latest && \
    go install -v github.com/OWASP/Amass/v3/...@master

# Install Ruby-based tools
RUN gem install wpscan

# Install Python-based tools
RUN pip install --no-cache-dir \
    sqlmap \
    wafw00f \
    arjun \
    dalfox \
    xsstrike \
    gitleaks \
    cmseek \
    retire

# Install Nikto
RUN git clone https://github.com/sullo/nikto.git /opt/nikto && \
    ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto

# Install testssl.sh
RUN git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl && \
    ln -s /opt/testssl/testssl.sh /usr/local/bin/testssl

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the SQLite DB is writable
RUN touch pentest_memory.db && chmod 666 pentest_memory.db

CMD ["python", "-m", "watchtower.main"]

