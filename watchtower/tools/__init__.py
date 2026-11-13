# Every tool Watchtower can drive. Each name has a wrapper module in this
# package with a run(target, **kwargs) function, and an install step in
# install_tools.sh.
ALL_TOOLS = (
    "nmap", "masscan", "httpx", "whatweb", "wafw00f",
    "subfinder", "amass", "dnsrecon", "nuclei", "nikto",
    "sqlmap", "wpscan", "testssl", "sslyze", "gobuster",
    "ffuf", "arjun", "xsstrike", "gitleaks", "cmseek",
    "retire", "dalfox", "kiterunner",
)
