# Watchtower

![Watchtower](https://raw.githubusercontent.com/fzn0x/watchtower/main/assets/imgs/watchtower.png){ width="640" }

**AI-powered penetration testing automation, orchestrated by LLM agents.**

Watchtower is a CLI that uses LLMs and [LangGraph](https://langchain-ai.github.io/langgraph/) to run agentic security assessments against websites you own or are authorized to test, then turns the results into pentest reports.

!!! warning "Authorized testing only"
    Penetration testing must only be performed with explicit permission. Watchtower does not enforce target scope; you are responsible for testing only systems you own or are authorized to assess. See [Legal](legal.md).

## How it works

A team of specialized agents reasons through the engagement in a loop:

- **Planner** looks at the target, current findings, and recent tool output, then picks the next tool or set of tools to run.
- **Worker** runs the requested tools, several at once when the planner asks for a parallel step.
- **Analyst** reviews every tool output from the step, filters false positives, and records structured findings.
- **Logic Analyst** reviews discovered endpoints and parameters for business-logic and IDOR risk and drafts a testing plan.

The loop repeats until the planner decides the assessment is complete.

## Features

- **28 integrated security tools** across network, web recon, crawling and URL discovery, DNS, vulnerability, TLS, content discovery, and secret scanning. See [Tools](tools.md).
- **Parallel reconnaissance**: independent tools run concurrently.
- **Smart truncation**: long tool output is clipped to keep security-relevant lines.
- **Run history in SQLite**, with per-run PDF reports. See [Reports](reports.md).
- **LLM-agnostic**: OpenAI, Gemini, OpenRouter, Anthropic, LiteLLM, or any OpenAI-compatible endpoint, with opt-in flagship models and reasoning controls. See [LLM providers](providers.md).

## Next steps

- [Install and configure Watchtower](getting-started.md)
- [Run your first scan](usage.md)
