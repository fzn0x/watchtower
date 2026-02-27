![Watchtower](assets/imgs/watchtower.png)

# 🏰 Watchtower (AI-Powered Penetration Testing Framework)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg?style=flat-square&logo=python)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/Architecture-LangGraph-orange.svg?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![LLMs](https://img.shields.io/badge/LLMs-Claude%20%7C%20Gemini%20%7C%20GPT-purple.svg?style=flat-square)]()

**Watchtower** is a simple AI-powered penetration testing automation CLI tool that leverages LLMs and LangGraph to orchestrate agentic workflows that you can use to test your websites locally. Generate useful pentest reports for your websites.

Penetration testing is red team activity and should be done with permission.

<p align="center">
  <br>
  <a href="#✨-core-features">Features</a> •
  <a href="#2-💻-installation">Installation</a> •
  <a href="#🚀-quick-start">Quick Start</a> •
  <a href="#❓-faq--troubleshooting">FAQ</a> •
  <a href="#📄-license">License</a>
</p>

## ⚠️ Legal Disclaimer

**Watchtower is designed exclusively for authorized security testing and educational purposes.**

- **Legal Use:** Authorized penetration testing, security research, educational environments.
- **Illegal Use:** Unauthorized access, malicious activities, any form of cyber attack.

You are fully responsible for ensuring you have explicit written permission before testing any system. Unauthorized access to computer systems is illegal under laws including the Computer Fraud and Abuse Act (CFAA), GDPR, and equivalent international legislation.

By using Watchtower, you agree to use it only on systems you own or have explicit authorization to test.

## ✨ Core Features

- **Multi-Agent Architecture**:
  - `Planner`: Analyzes the target and current findings to strategize the next sequence of actions.
  - `Worker`: Dynamically executes tools requested by the Planner.
  - `Analyst`: Parses tool stdout/stderr, filters false positives, and converts raw findings into structured schema data.
- **Dynamic Tool Arsenal**: Integrated with 23 security tools using Python subprocess wrappers. The interactive CLI auto-checks your PATH and lets you exclude tools dynamically.
  - *Network*: `nmap`, `masscan`
  - *Web Recon*: `httpx`, `whatweb`, `wafw00f`
  - *Subdomain*: `subfinder`, `amass`, `dnsrecon`
  - *Vulnerability*: `nuclei`, `nikto`, `sqlmap`, `wpscan`, `retire.js`
  - *SSL/TLS*: `testssl.sh`, `sslyze`
  - *Content/Params*: `gobuster`, `ffuf`, `arjun`, `kiterunner`
  - *Security Analysis*: `xsstrike`, `gitleaks`, `cmseek`, `dalfox`
- **State Management**: Uses `SQLite` locally to store a historical record of observations and findings.
- **LLM Agnostic**: Seamlessly swap between OpenAI, Google Gemini, and OpenRouter APIs via `.env` files.

---

## 🚀 Quick Start

### 1. 📋 Requirements & Prerequisites

**Prerequisites:**
- **OS**: Linux or macOS recommended (Windows supported via WSL2 for some networking tools).
- **Python**: 3.11+ installed.
- **API Keys**: An active API key for OpenRouter, OpenAI, or Gemini.

**Tool Requirements:**
To utilize the AI's full capabilities, you must have the actual CLI binaries installed and accessible in your system `PATH` (e.g., `nmap`, `nuclei`, `httpx`). The framework will automatically detect which tools are missing and skip them in the UI.

### 2. 💻 Installation

```bash
git clone https://github.com/fzn0x/watchtower.git
cd watchtower

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. ⚙️ Configuration

```bash
cp .env.example .env
```
Populate `.env` with your API keys. You only need to fulfill **one** of the API setups:
- `OPENAI_API_KEY=""`
- `GEMINI_API_KEY=""`
- `OPENROUTER_API_KEY=""`

*(Optional)* Explicitly define which model strings the framework should use. Defaults are already configured:
- `OPENAI_MODEL_NAME="gpt-4-turbo"` 
- `GEMINI_MODEL_NAME="gemini-1.5-pro"` 
- `OPENROUTER_MODEL_NAME="anthropic/claude-3-opus"` 

### 4. ▶️ Running the Framework

You **must** specify a target URL or IP using the `-t` or `--target` flag. 

```bash
python -m watchtower.main -t https://www.example.com
```

Upon execution, Watchtower will display an interactive CLI checkbox prompt. It automatically highlights which of the 23 tools are successfully installed on your machine. You can use `<Space>` to enable/disable specific tools allowing you to narrowly focus the LLM's payload, or hit `<Enter>` to confirm the selection.

**Headless Mode:**
If you want to bypass the interactive menu or are integrating Watchtower into an automated CI/CD pipeline, use the `--skip-ask-tools` flag to auto-run with everything available on your PATH:
```bash
python -m watchtower.main -t https://www.example.com --skip-ask-tools
```

## 🐳 Docker Deployment (Recommended)

To avoid "Missing tools" warnings and ensure all 23+ security utilities are correctly configured, we recommend running Watchtower via Docker.

### 1. Build the Image
```bash
docker-compose build
```

### 2. Run a Pentest
```bash
docker-compose run agentic-pentest python -m watchtower.main -t https://example.com
```

### 3. Generate a Report
```bash
docker-compose run agentic-pentest python -m watchtower.main --report pentest_report.pdf
```
The report will be saved to your local directory via the volume mount.


## 📊 Generating Reports

Watchtower automatically stores all executed commands, terminal outputs, and confirmed vulnerabilities in a local SQLite memory file (`pentest_memory.db`). 

You can extract all findings into a cleanly formatted PDF document without re-running the pentest:
```bash
python -m watchtower.main --report "pentest_report.pdf"
```

<img width="792" height="738" alt="image" src="https://github.com/user-attachments/assets/7264ec48-b48f-4419-8f44-5cc7ab821aaa" />


### 5. 🔌 Custom Providers

Watchtower dynamically supports almost any LLM provider on the market via LangChain and LiteLLM integrations. You can override the default models from the CLI using the `--provider`, `--model`, and `--apikey` flags.

```bash
 python -m watchtower.main -t https://www.example.com --provider=https://api.dgrid.ai --model=anthropic/claude-opus-4.5 --apikey "API_KEY"
```

Example response (using httpx tool):

```bash
INFO: ==> Node Executed: [WORKER]
INFO: HTTP Request: POST https://api.dgrid.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
INFO: ==> Node Executed: [ANALYST]
INFO:     - Updated state 'findings': [{'title': 'Overly Permissive CORS Configuration', 'severity': 'Medium', 'description': 'The server is configured with Access-Control-Allow-Origin: * which allows any website to make cross-origin requests to this domain. This could potentially allow malicious websites to interact with the API on behalf of authenticated users, leading to data theft or unauthorized actions if sensitive endpoints exist.', 'evidence': 'Access-Control-Allow-Origin: *\naccess-control-allow-headers: *\naccess-control-allow-methods: GET, HEAD, OPTIONS'}, {'title': 'Missing Security Headers', 'severity': 'Low', 'description': 'The response is missing several recommended security headers including X-Frame-Options (clickjacking protection), Content-Security-Policy (XSS and injection protection), and Strict-Transport-Security (HSTS for enforcing HTTPS). While some headers like X-Content-Type-Options and Referrer-Policy are present, the absence of these headers reduces the overall security posture.', 'evidence': 'HTTP/1.1 200 OK\nDate: Fri, 27 Feb 2026 13:28:07 GMT\nContent-Type: text/html; charset=utf-8\n[Headers present: x-content-type-options: nosniff, referrer-policy: strict-origin-when-cross-origin]\n[Missing: X-Frame-Options, Content-Security-Policy, Strict-Transport-Security]'}]
```

> ⚠️ **Disclaimer:** The `--apikey` argument requires the exact **property name** of the variable stored inside your `.env` file (e.g., `MY_GROQ_KEY`), *not* the raw API key string itself. This prevents your secrets from leaking into bash history.

**Supported Providers Include:**
- Anthropic
- OpenAI
- OpenRouter
- Litellm
- Amazon Bedrock
- Vercel AI Gateway
- Moonshot AI
- Mistral
- MiniMax
- OpenCode Zen
- GLM Models
- Z.AI
- Synthetic
- Qianfan
- **Any custom HTTP URLs** (Acts as a drop-in OpenAI-compatible endpoint, automatically routing requests via LangChain's `ChatOpenAI` client)
- Others: https://docs.litellm.ai/docs/providers

**Example CLI Execution (Custom Endpoint):**
```bash
python -m watchtower.main -t https://example.com --provider=https://api.dgrid.ai/api/v1 --model=anthropic/claude-opus-4.5 --apikey "API_KEY"
```

---

## 🗺️ Roadmap

- [x] Initial LangGraph Planner/Worker architecture.
- [x] Integrate core web and network reconnaissance tools.
- [x] Add Pydantic structured output fallback for open-source OpenRouter models.
- [ ] Add support for authenticated pentesting workflows (e.g cookie injection).

---

## 📌 Important Notes

- **API Costs**: The multi-agent workflow consumes tokens rapidly during active scanning as the Planner loops through observations. Be mindful of your API budgets.
- **Hallucinations**: While the Analyst agent filters false positives, LLMs can still hallucinate conclusions based on ambiguous tool outputs. **Always manually verify findings.**
- **Network Stability**: Some tools (like `masscan` or `ffuf`) are extremely noisy. You may trigger upstream edge-protections (Cloudflare) on your targets, which will pollute the observation logs with 403s.

---

## ❓ FAQ & Troubleshooting

### Q: `model: [model_name] does not support feature: structured-outputs`
This error occurs when using experimental, free, or unsupported models via OpenRouter (e.g. some Qwen or DeepSeek variants). Watchtower relies on LangChain's Structured Outputs mechanism to force the AI to return perfectly formatted JSON objects. If you see this error, switch your `OPENROUTER_MODEL_NAME` in the `.env` file to a fully-supported model like:
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4o`
- `google/gemini-1.5-pro`
- `meta-llama/llama-3.1-70b-instruct`

*Note: The framework includes a custom string-fallback parser for models that don't natively support API structured outputs, but using supported commercial models yields significantly better pentesting logic.*

### Q: `429 Too Many Requests: [model]:free is temporarily rate-limited upstream`
This means you are using an explicitly `:free` model tier on OpenRouter, and the upstream providers (like Venice or Novita) are currently rate-limiting free-tier requests due to high global traffic. You simply need to wait out the timeout or switch to a slightly different (or paid) model endpoint.

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

By using this software, you agree to the conditions outlined in the [Legal Disclaimer](#-legal-disclaimer). Watchtower's developers assume no liability for the misuse of this tool.

---

## 🙏 Author & Acknowledgements

Created and maintained by **[fzn0x](https://github.com/fzn0x)**.

A deep and sincere thank you to the open-source security community. Watchtower stands on the shoulders of giants—this framework would not exist without the incredible developers who built and maintain the underlying penetration testing and reconnaissance tools that power the core worker engine. Thank you for making security accessible.
