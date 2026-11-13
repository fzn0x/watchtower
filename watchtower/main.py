import argparse
import logging
import os
from dotenv import load_dotenv
import questionary
import shutil

from watchtower import __version__
from watchtower.core.agent_manager import create_agent_graph
from watchtower.core.memory import MemoryStore
from watchtower.core.guardrails import validate_target

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="AI Agentic Pentesting Framework")
    parser.add_argument("--version", action="version", version=f"watchtower {__version__}")
    parser.add_argument("-t", "--target", help="Target URL or IP", required=False)
    parser.add_argument("--skip-ask-tools", action="store_true", help="Skip tool selection")
    parser.add_argument("--provider", help="Custom LLM provider (e.g. litellm, openai, anthropic, bedrock, etc.)")
    parser.add_argument("--model", help="Custom model string")
    parser.add_argument("--apikey", help="Environment variable name containing the API key (e.g. GROQ_API_KEY)")
    parser.add_argument("--report", help="Generate a PDF report from the SQLite database (provide output filename, e.g. report.pdf)")
    parser.add_argument("--run", help="Run id to report on (defaults to the most recent run). Used with --report.")
    parser.add_argument("--cookie", help="Session cookie to use for authenticated requests")
    parser.add_argument("--header", action="append", help="Custom headers (format Key:Value). Can be specified multiple times.")
    parser.add_argument("--flagship", action="store_true", help="Use the provider's flagship model with reasoning at high effort.")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="Reasoning effort for models that support it (each provider accepts a subset).")
    parser.add_argument("--max-tokens", type=int, dest="max_tokens", help="Maximum output tokens for the model.")
    args = parser.parse_args()

    auth_metadata = {}
    if args.cookie:
        auth_metadata["Cookie"] = args.cookie
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                auth_metadata[k.strip()] = v.strip()

    if args.provider:
        os.environ["WATCHTOWER_PROVIDER"] = args.provider
    if args.model:
        os.environ["WATCHTOWER_MODEL"] = args.model
    if args.apikey:
        os.environ["WATCHTOWER_APIKEY_NAME"] = args.apikey
    if args.flagship:
        os.environ["WATCHTOWER_FLAGSHIP"] = "1"
    if args.effort:
        os.environ["WATCHTOWER_EFFORT"] = args.effort
    if args.max_tokens:
        os.environ["WATCHTOWER_MAX_TOKENS"] = str(args.max_tokens)

    if args.report:
        from watchtower.reporting.reporter import generate_pdf_report
        import sys
        
        output_file = args.report if args.report.endswith(".pdf") else args.report + ".pdf"
        generate_pdf_report("pentest_memory.db", output_file, run_id=args.run)
        sys.exit(0)

    if not args.target:
        parser.error("The -t/--target argument is required unless you are generating a report.")

    if not validate_target(args.target):
        logging.error(f"Invalid target provided: {args.target}")
        logging.error("Target must be a valid URL or IP address.")
        return

    logging.info(f"Initializing Watchtower {__version__} (Agentic Pentesting Framework)...")
    if args.flagship or args.effort or args.max_tokens:
        logging.info(
            "LLM runtime: flagship=%s, effort=%s, max_tokens=%s",
            bool(args.flagship), args.effort or "default", args.max_tokens or "default",
        )

    all_tools = [
        "nmap", "masscan", "httpx", "whatweb", "wafw00f",
        "subfinder", "amass", "dnsrecon", "nuclei", "nikto",
        "sqlmap", "wpscan", "testssl", "sslyze", "gobuster",
        "ffuf", "arjun", "xsstrike", "gitleaks", "cmseek",
        "retire", "dalfox", "kiterunner"
    ]
    selected_tools = all_tools.copy()
    
    if not args.skip_ask_tools:
        # Some tools are invoked under a different binary name than their key.
        binary_aliases = {
            "testssl": ["testssl.sh"],
            "kiterunner": ["kr"],
        }

        def is_installed(t):
            candidates = [t] + binary_aliases.get(t, [])
            return any(shutil.which(name) for name in candidates)

        installed_tools = [tool for tool in all_tools if is_installed(tool)]
        missing_tools = [tool for tool in all_tools if not is_installed(tool)]
        
        if missing_tools:
            logging.warning(f"Missing tools: {', '.join(missing_tools)}")
            
        choices = [
            questionary.Choice(tool, checked=(tool in installed_tools))
            for tool in all_tools
        ]
        
        try:
            answers = questionary.checkbox(
                "Select which tools the AI is allowed to use for this pentest:",
                choices=choices
            ).ask()
            if answers is not None:
                selected_tools = answers
            else:
                logging.info("Aborted.")
                return
        except Exception as e:
            logging.warning(f"Interactive prompt failed. Falling back to installed tools.")
            selected_tools = installed_tools
            
    logging.info(f"Selected tools: {', '.join(selected_tools)}")
    memory = MemoryStore("pentest_memory.db")
    run_id = memory.start_run(args.target)
    logging.info(f"Memory database initialized (SQLite). Run id: {run_id}")
    
    graph = create_agent_graph()
    logging.info("Multi-agent state graph compiled successfully.")
    
    initial_state = {
        "scope_targets": [args.target],
        "available_tools": selected_tools,
        "messages": [],
        "findings": [],
        "observations": [],
        "latest_observations": [],
        "current_plan": "",
        "next_step": "",
        "auth_metadata": auth_metadata,
        "is_finished": False
    }
    
    logging.info(f"Starting agent execution loop against target: {args.target}")
    logging.info("-" * 40)
    for event in graph.stream(initial_state, config={"recursion_limit": 100}):
        for node_name, state_updates in event.items():
            logging.info(f"==> Node Executed: [{node_name.upper()}]")
            
            # Save raw tool results to SQLite Memory
            if "observations" in state_updates:
                for obs in state_updates["observations"]:
                    memory.log_observation(obs.get("target"), obs.get("tool"), obs.get("output"))
            
            # Save confirmed vulnerabilities to SQLite Memory
            if "findings" in state_updates:
                for finding in state_updates["findings"]:
                    target = finding.get("target", args.target)
                    vulnerability = finding.get("title", "Unknown Finding")
                    memory.log_finding(target, vulnerability, finding)
            
            for key, val in state_updates.items():
                if key not in ["messages", "observations", "latest_observations"]:
                    logging.info(f"    - Updated state '{key}': {val}")
    
    logging.info("-" * 40)
    logging.info("Pentest execution loop complete.")

if __name__ == "__main__":
    main()
