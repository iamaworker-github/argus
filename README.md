# Argus - AI-Powered Security Testing Platform

```
     █████╗ ██████╗  ██████╗ ██╗   ██╗███████╗
    ██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝
    ███████║██████╔╝██║  ███╗██║   ██║███████╗
    ██╔══██║██╔══██╗██║   ██║██║   ██║╚════██║
    ██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝
```

> **See Everything. Miss Nothing.**  
> AI-powered autonomous security testing platform — **80+ integrated tools, zero dependency issues**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)]()
[![Tools](https://img.shields.io/badge/Tools-80%2B-00FF88.svg)]()

## Quick Install

```bash
# Docker (recommended — zero dependencies)
docker pull ghcr.io/iamaworker-github/argus:latest
docker run --rm -it -v $(pwd):/work ghcr.io/iamaworker-github/argus:latest strix -t https://example.com

# One-liner installer
curl -fsSL https://raw.githubusercontent.com/iamaworker-github/argus/main/scripts/install.sh | bash

# Native Python (requires Python 3.11+)
git clone https://github.com/iamaworker-github/argus.git
cd argus && bash scripts/install.sh --native
```

## 🚀 Features

### Core
- **Multi-Agent Architecture**: Deploys specialized AI agents for each attack vector in parallel
- **80+ Integrated Tools**: nmap, nuclei, sqlmap, ffuf, subfinder, httpx, holehe, maigret, sherlock, trufflehog, gitleaks, rustscan, testssl.sh, dnstwist, certipy, responder, prowler, trivy, mobsf, frida, binwalk, volatility, peass, chisel, impacket, kerbrute, and more
- **Strix-Compatible**: Full Strix CLI interface with scan modes, skills system, AI-driven planning
- **LLM Integration**: OpenAI, Anthropic, OpenCode (DeepSeek V4), Google AI, Groq, LiteLLM
- **Zero Dependency Docker**: All tools pre-baked in Docker image, no pip/apt install needed
- **Dan级 Scanning (Deep+Slow+Accurate)**: White-box source-sink analysis, temporal orchestration, professional reports

### Security Testing
- **Injection Flaws**: SQL, NoSQL, Command Injection, SSTI
- **XSS**: Reflected, Stored, DOM-based, Blind XSS
- **SSRF**: Internal network access, cloud metadata, port scanning
- **Authentication**: Weak credentials, session management, OAuth, 2FA, JWT attacks
- **Access Control**: IDOR, privilege escalation, mass assignment
- **Cloud Security**: Prowler (AWS/Azure/GCP), ScoutSuite, Trivy (containers/K8s/IaC)
- **Active Directory**: Certipy, BloodHound, Kerbrute, Impacket, NetExec, Responder
- **Mobile Security**: MobSF (APK/IPA analysis), Frida (dynamic instrumentation)
- **OSINT**: Holehe (email), Maigret (username 3000+ sites), Sherlock, SpiderFoot, theHarvester

### Scanning Modes
| Mode | Duration | Depth | Use Case |
|---|---|---|---|
| `quick` | 5-15 min | Surface scan | CI/CD gate |
| `standard` | 30-60 min | Standard depth | Bug bounty triage |
| `deep` | 1-4 hrs | Full coverage | Pentest engagement |
| `whitebox` | varies | Source-sink analysis | Code review |

## 📦 Docker Usage

```bash
# Pull and run
docker pull ghcr.io/iamaworker-github/argus:latest

# Quick web recon
docker run --rm -it -v $(pwd):/work \
  ghcr.io/iamaworker-github/argus:latest strix -t https://example.com -m quick

# Deep pentest with Docker socket (for tool_runner)
docker run --rm -it \
  -v $(pwd):/work \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e LLM_API_KEY="your-key" \
  ghcr.io/iamaworker-github/argus:latest strix -t https://example.com -m deep

# API mode
docker run --rm -d -p 8484:8484 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  ghcr.io/iamaworker-github/argus:latest api

# Docker compose (with Redis + Neo4j)
docker compose --profile memory up -d
```

## 🛠 Tool Registry

Argus v3 has a centralized tool registry with **84 indexed tools**:

```bash
# List all tools by category
docker run --rm ghcr.io/iamaworker-github/argus:latest python3 -c "
from argus.core.tool_runner import ToolRunner
r = ToolRunner()
print('Categories:', r.list_categories())
print('Workflows:', list(r.get_workflows().keys()))
"
```

### Built-in Workflows

| Workflow | Chain |
|---|---|
| `recon` | subfinder → httpx → nuclei → amass |
| `web_audit` | httpx → nuclei → ffuf → gobuster → wafw00f → testssl |
| `osint_email` | holehe → theharvester → infoga |
| `osint_username` | maigret → sherlock → socialscan |
| `secret_scan` | trufflehog → gitleaks → gitdork |
| `ad_assessment` | bloodhound → certipy → kerbrute → impacket → netexec → responder |
| `cloud_audit` | prowler → scoutsuite → pacu → trivy |
| `mobile_test` | mobsf → frida → objection → jadx |
| `forensics` | volatility → binwalk → pspy |
| `tls_audit` | testssl → nuclei -tags ssl,tls |
| `port_scan` | masscan → rustscan → nmap |
| `web_fuzz` | ffuf → gobuster → dirsearch → arjun |

### Docker Image Overrides

All external tools automatically run through purpose-built Docker images when available:

```python
from argus.core.tool_runner import ToolRunner
runner = ToolRunner()
result = await runner.execute("information_gathering.Holehe", args="user@example.com")
# Auto-detects Docker, pulls megadose/holehe, runs, returns structured JSON
```

## 🤖 Architecture

```
User Input → PlanAgent (LLM analyzes target)
                  ↓
          Agent Orchestrator
           /    |    |    \
    WebAgent  NetworkAgent  OSINTAgent  CloudAgent ...
      |          |            |            |
    nuclei     nmap        holehe       prowler
    sqlmap     rustscan    maigret      trivy
    ffuf       testssl     sherlock     scoutsuite
    ...        ...         ...          ...

    All tools execute via ToolRunner → Docker (preferred) / Native
    Results → Blackboard → Graph Memory → Professional Report
```

## 📋 Requirements

- **Docker** (recommended) or **Python 3.11+** (native)
- **API Keys**: OpenAI / Anthropic / OpenCode (for AI features)

## 🔧 Native Install

```bash
git clone https://github.com/iamaworker-github/argus.git
cd argus
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m playwright install chromium
```

## 📚 Claude Code Agents

43 specialized AI agents for Claude Code:

```bash
bash scripts/install.sh --global
```

## 🏗 Project Structure

```
argus/
├── agents/              AI-powered security agents
│   ├── plan_agent.py    Target analysis & agent selection (LLM)
│   ├── nuclei_agent.py  Template-based vulnerability scanning
│   ├── exploitation_agent.py  Auto-exploitation engine
│   ├── osint/           OSINT intelligence agents
│   └── pentest/         Pentest-specific agents
├── core/
│   ├── tool_runner.py   Unified tool execution (Docker/Native)
│   ├── tool_system.py   Typed tool registry with 26 registered tools
│   ├── json_utils.py    Robust LLM JSON extraction
│   └── config.py        Configuration management
├── data/
│   └── tools.json       84-tool central index with Docker mappings
├── toolkit/
│   ├── browser.py       Playwright automation
│   ├── tools/           New tool wrappers (osint, ad, cloud, mobile, forensics)
│   └── shell.py         Sandboxed command execution
├── skills/              Agent skill knowledge packages
└── Dockerfile           Production multi-stage build
```

## 📄 License

Apache 2.0. See [LICENSE](LICENSE).

> **For authorized security testing, bug bounty, CTFs, and research only.**
