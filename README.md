# Argus — AI-Powered Autonomous Pentest Platform

```
     █████╗ ██████╗  ██████╗ ██╗   ██╗███████╗
    ██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝
    ███████║██████╔╝██║  ███╗██║   ██║███████╗
    ██╔══██║██║══██╗██║   ██║██║   ██║╚════██║
    ██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝
```

> **See Everything. Miss Nothing.**
> Argus is an AI-powered autonomous security testing platform with 30+ specialized agents, 80+ integrated tools, and self-learning capabilities. It plans, executes, and learns from security assessments — no manual configuration needed.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Pull-2496ED.svg?logo=docker)](https://hub.docker.com/r/iamaworker135/argus)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-181717.svg?logo=github)](https://github.com/iamaworker-github/argus)

---

## Features

- **🤖 30+ Specialized AI Agents** — Each attack vector gets a dedicated agent (SQLi, XSS, SSRF, JWT, IDOR, LFI, RCE, etc.)
- **🧠 Self-Learning Skill System** — Auto-learns successful attack patterns as reusable skills with confidence scoring
- **🎯 MCTS Attack Planning** — Monte Carlo Tree Search prioritizes the most promising attack paths
- **🌐 Web Dashboard** — Real-time scan monitoring, technology filtering, session persistence
- **🔗 Cross-Agent Chaining** — SSRF → internal pivot, SQLi → data extraction, IDOR → auth bypass
- **📊 Dual Knowledge Graph** — Attack surface topology + temporal evolution tracking
- **🛡️ 80+ Integrated Tools** — nmap, nuclei, pd-httpx, sqlmap, ffuf, gau, katana, waybackurls, and more
- **🔑 Auth Propagation** — Headers/cookies flow through every agent automatically
- **📈 4 Scan Modes** — quick (5min), standard (30min), deep (4hr), whitebox

---

## Quick Start

### Docker (recommended)

```bash
docker pull iamaworker135/argus:latest

# Web dashboard
docker run -d -p 8484:8484 \
  -e LLM_API_KEY="sk-your-key" \
  iamaworker135/argus:latest

# Quick scan
docker run --rm \
  -e LLM_API_KEY="sk-your-key" \
  iamaworker135/argus:latest \
  strix --target https://testfire.net -m quick

# Full pentest with auth
docker run --rm \
  -e LLM_API_KEY="sk-your-key" \
  -e ARGUS_AUTH_HEADERS='{"Authorization": "Bearer eyJ..."}' \
  iamaworker135/argus:latest \
  strix --target https://example.com -m deep
```

### One-line Native Install (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/iamaworker-github/argus/main/install.sh | bash
```

Auto-installs: Python venv, pd-httpx, naabu, nuclei, katana, gau, waybackurls, nmap, web dashboard.

---

## Scan Modes

| Mode | Duration | Description |
|------|----------|-------------|
| `quick` | 5-15 min | Surface scan — CI/CD gate, low-hanging fruit |
| `standard` | 30-60 min | Standard depth — bug bounty triage |
| `deep` | 1-4 hrs | Full coverage — pentest engagement |
| `whitebox` | varies | Source-sink analysis — code review |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Planner Layer                            │
│  MCTS Planner ──► Goal Tree ──► Agent Composer ──► Skills  │
├─────────────────────────────────────────────────────────────┤
│                     Execution Layer                          │
│  Phase 1: AI Planning    Phase 5: Vuln Testing (21 agents) │
│  Phase 2: Reconnaissance  Phase 6: AI Analysis             │
│  Phase 3: Enumeration     Phase 7: Exploitation            │
│  Phase 4: Service Scan    Phase 8: Reporting               │
├─────────────────────────────────────────────────────────────┤
│                     Intelligence Layer                       │
│  Meta-Cognition ──► Budget Controller ──► Skill Library     │
│  Context Injector ──► Cross-Agent Chaining ──► EvoGraph    │
├─────────────────────────────────────────────────────────────┤
│                     Infrastructure                           │
│  Web Dashboard ──► Event Bus ──► Memory ──► Auth Provider  │
│  Sandbox ──► Tool Registry ──► LLM Client ──► MCP Server   │
└─────────────────────────────────────────────────────────────┘
```

### Vulnerability Coverage

| Category | Tests |
|----------|-------|
| **Injection** | SQL, NoSQL, Command, SSTI, LDAP |
| **XSS** | Reflected, Stored, DOM-based, Blind |
| **SSRF** | Internal network, cloud metadata, port scan |
| **Auth** | JWT attacks, weak credentials, session, OAuth |
| **Access Control** | IDOR, privilege escalation, CORS |
| **Infra** | Clickjacking, open redirect, host header, rate limit |

---

## Web Dashboard

Open `http://localhost:8484` after starting:

```bash
docker run -d -p 8484:8484 iamaworker135/argus:latest
```

Features: real-time scan logs, technology filtering, attack graph visualization, session management, report export.

---

## Configuration

```bash
# Required: LLM provider
export LLM_API_KEY="sk-your-key"

# Optional: model selection
export LLM_MODEL="openai/gpt-4o"

# Auth propagation
export ARGUS_AUTH_HEADERS='{"Authorization": "Bearer eyJ..."}'
export ARGUS_AUTH_COOKIES='{"session": "abc123"}'

# Scan behavior
export USE_DOCKER=false
export SCAN_DEPTH=deep
```

---

## Build from Source

```bash
git clone https://github.com/iamaworker-github/argus.git
cd argus

# Docker
docker build -t argus:latest .

# Native
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ".[web]"
argus --help
```

---

## Project Structure

```
argus/
├── agents/              30+ specialized AI agents
│   ├── modes/pentest.py 8-stage orchestrator
│   ├── base_agent.py    Shared agent infrastructure
│   ├── cms/             CMS-specific agents (WP, Drupal, Joomla...)
│   ├── stack/           Stack-specific agents (Node, Flask, Spring...)
│   └── iot_agent.py     IoT security agent
├── core/                Intelligence & infrastructure
│   ├── mcts_planner.py  Monte Carlo Tree Search
│   ├── goal_tree.py     Recursive goal decomposition
│   ├── agent_composer.py Dynamic agent assembly
│   ├── skill_library.py Auto-learning skill system
│   ├── budget_controller.py Per-agent budget enforcement
│   ├── meta_cognition.py Self-reflection & strategy shift
│   ├── context_injector.py Dynamic target context
│   ├── evograph.py      Dual knowledge graph
│   ├── sandbox.py       Docker sandbox pool
│   └── ...              ACI, runbooks, confidence, fix pipeline
├── web-dashboard/       React + Vite dashboard
├── toolkit/             Tool management & installation
├── skills/              Attack skill knowledge base
├── benchmarks/          Benchmark suites (4 suites, 9 tests)
├── Dockerfile           Single-stage Ubuntu + Go + Python
└── install.sh           One-curl installer
```

---

## Docker Hub

Pre-built images available at [iamaworker135/argus](https://hub.docker.com/r/iamaworker135/argus):

- `latest` — latest stable release
- `v2.0.0` — versioned release

---

## Use Cases

- **CI/CD Security Gate** — `quick` mode blocks critical/high findings in CI pipelines
- **Bug Bounty Triage** — `standard` mode finds low-hanging fruit fast
- **Pentest Engagement** — `deep` mode with full-chain exploitation
- **Continuous Monitoring** — Web dashboard with scheduled scans
- **CTF Automation** — Autonomous flag capture via multi-agent coordination

---

## License

Apache 2.0. See [LICENSE](LICENSE).

> **For authorized security testing, bug bounty, CTFs, and research only.**

## ⚠️ Warning

This tool performs active security testing that may disrupt target services. Always obtain written authorization before testing. Unauthorized access is illegal.
