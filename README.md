# Argus - AI-Powered Autonomous Pentest Platform

```
     █████╗ ██████╗  ██████╗ ██╗   ██╗███████╗
    ██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝
    ███████║██████╔╝██║  ███╗██║   ██║███████╗
    ██╔══██║██╔══██╗██║   ██║██║   ██║╚════██║
    ██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝
```

> **See Everything. Miss Nothing.**
> AI-powered autonomous security testing platform — **80+ integrated tools, 30+ specialized agents**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)]()
[![Tools](https://img.shields.io/badge/Tools-80%2B-00FF88.svg)]()

## Pipeline

```
AI Planning ──► Reconnaissance ──► Enumeration ──► Vulnerability ──► AI Analysis ──► Exploitation ──► Reporting
     │                │                  │                │                │                 │               │
  LLM target      WAF detect        BackMeUp         21 web vuln      AI prioritizes    Auto-exploit    Markdown/
  analysis        httpx -td         SmartBruteForce  agents + nuclei  + false-pos        with PoC        J/JSON/HTML
  plan gen        nmap -p-          svc enum -sV -sC  validate (curl)  reduce + skill    propagation     dashboard
```

### Phase Details

| Phase | Agents | Description |
|---|---|---|
| **1. AI Planning** | PlanAgent | LLM analyzes target, generates attack plan, selects agents |
| **2. Reconnaissance** | WAFDetectionAgent, ReconAgent, NucleiAgent | WAF detection, httpx tech detection (-td), nmap all-ports (-p-), nuclei templates |
| **3. Enumeration** | BackMeUpAgent, SmartBruteForceAgent, service enum | URL harvesting (gau/katana/waybackurls), path bruteforce, nmap -sV -sC on open ports |
| **4. Vulnerability** | 21 specialized agents + PoCValidatorAgent | SQLi, XSS, SSRF, CSRF, SSTI, JWT, IDOR, LFI, RCE, CORS, XXE, clickjacking, open redirect, host header injection, rate limiting, NoSQL injection + curl PoC validation |
| **5. AI Analysis** | AnalysisAgent | Cross-correlates findings, deduplicates, false-positive reduction, auto-learns skills from H1 disclosures |
| **6. Exploitation** | ExploitationAgent | Auto-exploitation with auth context, credential propagation |
| **7. Reporting** | ReportAgent | Professional markdown/JSON/HTML reports with proof snippets |

## Features

### Core
- **7-Stage Pipeline**: AI Planning → Recon → Enumeration → Vulnerability → AI Analysis → Exploitation → Reporting
- **30+ Specialized AI Agents**: Each attack vector gets a dedicated agent with targeted tooling
- **80+ Integrated Tools**: nmap, nuclei, sqlmap, ffuf, httpx, gau, katana, waybackurls, and more
- **Auth Propagation**: Auth headers/cookies flow through every agent — recon, nuclei, enumeration, all vulnerability agents
- **True-Positive Validation**: Independent curl-based reproduction (BountyGrimoire-inspired) before Python sandbox execution
- **H1 Skill Learning**: Auto-fetches HackerOne disclosed reports, extracts payloads + remediations, generates `.md` skill files
- **Autonomous Learning**: Self-improving skill system — learns from every scan and public disclosures
- **LLM Integration**: OpenAI, Anthropic, OpenCode (DeepSeek V4), Google AI, Groq, LiteLLM
- **Zero Dependency Docker**: All tools pre-baked in single Docker image, no pip/apt install needed
- **Cross-Session Memory**: Blackboard + graph database stores findings, credentials, tech stack across scans

### Vulnerability Coverage
- **Injection**: SQL, NoSQL, Command Injection, SSTI, LDAP Injection
- **XSS**: Reflected, Stored, DOM-based, Blind XSS
- **SSRF**: Internal network, cloud metadata, port scanning
- **Authentication**: JWT attacks, weak credentials, session management, OAuth
- **Access Control**: IDOR, privilege escalation, CORS misconfiguration
- **Infrastructure**: Clickjacking, open redirect, host header injection, rate limiting
- **Cloud**: Prowler (AWS/Azure/GCP), ScoutSuite, Trivy (containers/K8s/IaC)
- **Active Directory**: Certipy, BloodHound, Kerbrute, Impacket, NetExec, Responder
- **Mobile**: MobSF (APK/IPA analysis), Frida (dynamic instrumentation)

### Scanning Modes
| Mode | Duration | Depth | Use Case |
|---|---|---|---|
| `quick` | 5-15 min | Surface scan | CI/CD gate |
| `standard` | 30-60 min | Standard depth | Bug bounty triage |
| `deep` | 1-4 hrs | Full coverage | Pentest engagement |
| `whitebox` | varies | Source-sink analysis | Code review |

## Quick Start

### One-line Install (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/iamaworker-github/argus/main/install.sh | bash
```

Auto-installs: Python venv, pd-httpx, naabu, nuclei, katana, gau, waybackurls, nmap, web dashboard & all dependencies.

### Docker (recommended)

```bash
docker pull ghcr.io/iamaworker-github/argus:latest

# Quick scan
docker run --rm -it -v $(pwd):/work \
  ghcr.io/iamaworker-github/argus:latest strix -t https://example.com -m quick

# Deep pentest with AI
docker run --rm -it \
  -v $(pwd):/work \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e LLM_API_KEY="your-key" \
  ghcr.io/iamaworker-github/argus:latest strix -t https://example.com -m deep
```

## Auth Propagation

Pass authenticated context to every agent:

```bash
export ARGUS_AUTH_HEADERS='{"Authorization": "Bearer eyJ..."}'
export ARGUS_AUTH_COOKIES='{"session": "abc123"}'

# Auth headers flow to: httpx -td, nuclei -H, gau, katana, waybackurls, path bruteforce
docker run --rm -it \
  -e ARGUS_AUTH_HEADERS="$ARGUS_AUTH_HEADERS" \
  -e ARGUS_AUTH_COOKIES="$ARGUS_AUTH_COOKIES" \
  ghcr.io/iamaworker-github/argus:latest strix -t https://example.com
```

## Web Dashboard

```bash
# Start API + web interface on port 8484
docker run --rm -d -p 8484:8484 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  ghcr.io/iamaworker-github/argus:latest api

# Open http://localhost:8484
```

## Build from Source

```bash
git clone https://github.com/iamaworker-github/argus.git
cd argus
docker build -t argus:latest .
```

## Native Install

### Automatic (install.sh)

```bash
curl -fsSL https://raw.githubusercontent.com/iamaworker-github/argus/main/install.sh | bash
```

### Manual

```bash
git clone https://github.com/iamaworker-github/argus.git
cd argus
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m playwright install chromium
```

## Project Structure

```
argus/
├── agents/                30+ specialized AI agents
│   ├── modes/
│   │   └── pentest.py    7-stage pipeline orchestrator
│   ├── base_agent.py     Auth propagation, HTTP client helpers
│   ├── plan_agent.py     LLM-based target analysis & planning
│   ├── recon_agent.py    Tech detection (httpx -td), headers
│   ├── waf_detection_agent.py  WAF detection & fingerprinting
│   ├── nuclei_agent.py   Batch nuclei template scanning
│   ├── poc_validator_agent.py  Curl-based independent validation
│   ├── backmeup_agent.py(gau/katana/waybackurls harvester)
│   ├── smart_bruteforce_agent.py  Auth-aware path bruteforce
│   ├── sql_injection_agent.py
│   ├── xss_agent.py
│   ├── ssrf_agent.py
│   ├── jwt_attack_agent.py
│   ├── cors_agent.py
│   ├── clickjacking_agent.py
│   ├── host_header_injection_agent.py
│   ├── open_redirect_agent.py
│   ├── rate_limit_agent.py
│   ├── ssti_agent.py
│   ├── xxe_agent.py
│   ├── nosql_injection_agent.py
│   └── ... (21+ vulnerability agents)
├── core/
│   ├── skill_learner.py  H1 disclosure fetcher, skill generator
│   ├── tool_runner.py    Unified tool execution (Docker/Native)
│   ├── tool_system.py    Typed tool registry
│   └── json_utils.py     Robust LLM JSON extraction
├── data/
│   └── tools.json        84-tool central index
├── toolkit/
│   └── backmeup_agent.py URL harvesting toolkit
├── skills/               Agent skill knowledge packages
├── web-dashboard/        React-based web UI (port 8484)
├── Dockerfile            Multi-stage: Node 22 + Ubuntu 24.04 + Go
└── README.md
```

## Use Cases

| Use Case | Mode | Expected |
|---|---|---|
| **CI/CD Security Gate** | quick | 5-15 min, blocks critical + high findings |
| **Bug Bounty Triage** | standard | 30-60 min, finds low-hanging fruit fast |
| **Pentest Engagement** | deep | 1-4 hrs, full-chain exploitation |
| **CTF Automation** | deep | Stages attacks, flags all services |
| **Continuous Monitoring** | API mode | Scheduled scans, web dashboard |

## License

Apache 2.0. See [LICENSE](LICENSE).

> **For authorized security testing, bug bounty, CTFs, and research only.**

## ⚠️ WARNING

This tool performs active security testing that may disrupt target services. Always obtain written authorization before testing. Unauthorized access is illegal.
