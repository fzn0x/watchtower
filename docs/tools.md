# Tools

Watchtower drives these tools through small Python wrappers. Each wrapper gets the target in the form the tool expects: a bare **host** for network, DNS, and TLS tools, or a full **URL** for web tools. The planner only chooses among the tools you allow and that are installed.

## Network

| Tool | Target | What Watchtower runs |
| --- | --- | --- |
| `nmap` | host | `nmap -sV -sC -A -Pn -T4 <host>` |
| `masscan` | host | `masscan -p1-65535 --rate 1000 <host>` |

## Web recon

| Tool | Target | What Watchtower runs |
| --- | --- | --- |
| `httpx` | URL | `httpx -u <url> -silent -nc -sc -title -td -server -cl -fr` (ProjectDiscovery's prober; see [Troubleshooting](troubleshooting.md#httpx-reports-could-not-run-or-is-shown-as-missing)) |
| `whatweb` | URL | `whatweb -a 3 <url>` |
| `wafw00f` | URL | `wafw00f -a <url>` |

## Subdomains and DNS

| Tool | Target | What Watchtower runs |
| --- | --- | --- |
| `subfinder` | host | `subfinder -d <host> -silent -all` |
| `amass` | host | `amass enum -passive -d <host>` |
| `dnsrecon` | host | `dnsrecon -d <host>` |

## Vulnerability scanning

| Tool | Target | What Watchtower runs |
| --- | --- | --- |
| `nuclei` | URL | `nuclei -u <url> -silent` |
| `nikto` | URL | `nikto -h <url> -maxtime 5m` |
| `sqlmap` | URL | `sqlmap -u <url> --batch --random-agent --level=2 --risk=2 --crawl=2` |
| `wpscan` | URL | `wpscan --url <url> --no-banner --random-user-agent --enumerate vp,vt,tt,cb,dbe,u,m` |
| `retire` | URL | `retire --site <url> --outputformat text` |

## TLS

| Tool | Target | What Watchtower runs |
| --- | --- | --- |
| `testssl` | host | `testssl.sh --quiet <host>` |
| `sslyze` | host | `sslyze <host>` |

## Content and parameter discovery

| Tool | Target | What Watchtower runs |
| --- | --- | --- |
| `gobuster` | URL | `gobuster dir -u <url> -w <wordlist>` |
| `ffuf` | URL | `ffuf -u <url>/FUZZ -w <wordlist> -t 40 -c` |
| `arjun` | URL | `arjun -u <url> -t 10 -T 5` |
| `kiterunner` | URL | `kr scan <url> -A=apiroutes-2202` |

`gobuster` and `ffuf` use `WATCHTOWER_WORDLIST` if set, then common SecLists/dirb locations, then a small list bundled with Watchtower.

## Security analysis

| Tool | Target | What Watchtower runs |
| --- | --- | --- |
| `xsstrike` | URL | `xsstrike -u <url>` |
| `dalfox` | URL | `dalfox url <url> --silence --skip-bav` |
| `cmseek` | URL | `cmseek -u <url> --batch --random-agent` |
| `gitleaks` | git repository URL | clones the repository to a temporary directory, then `gitleaks detect --source <dir> -v`; skipped for non-repository targets |

## Authenticated requests

`--cookie` and `--header` values are forwarded to the tools that accept request headers (for example `httpx` and `sqlmap`).

## Adding a tool

See [Development](development.md#adding-a-tool).
