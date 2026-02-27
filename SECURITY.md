# Security Policy

## Supported Versions

Currently, only the `main` branch is actively supported with security updates. We recommend frequently pulling the latest changes.

| Version | Supported          |
| ------- | ------------------ |
| `main`  | :white_check_mark: |
| Older   | :x:                |

## Reporting a Vulnerability

Watchtower is a security tool, and we take its own security seriously. 

If you discover a vulnerability in Watchtower that could lead to unauthorized code execution, bypass the intended LLM-sandbox constraints, or expose user API keys, please do **not** report it by creating a public GitHub issue.

Instead, please issue a pull request with the fix.

Please include the following in your report:
1. A detailed description of the vulnerability.
2. Step-by-step instructions or an exploit PoC to reproduce the bug.
3. The potential impact if exploited.

### Response Timeline
- We will acknowledge receipt of your vulnerability report within 48 hours.
- We aim to provide a status update and potential mitigation strategy within 5 business days.
- A patch and CVE (if applicable) will be released as quickly as possible upon confirmation.

### Out of Scope
The following issues are considered out of scope for this repository's security disclosure:
- Issues related to the third-party upstream CLI tools themselves (e.g., a buffer overflow in the Nmap binary). Please report those directly to the tool's respective maintainers.
- AI Hallucinations: If the LLM generates an inaccurate pentest report, this is a known limitation of generative AI and not considered a security vulnerability of the framework code.
- "Jailbreaks" of the underlying LLM providers (e.g. bypassing Anthropic's safety filters).

Thank you for helping keep Watchtower safe!
