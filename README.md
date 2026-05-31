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
> Argus is an AI-powered autonomous security testing platform with **60+ specialized agents**, **150+ hacking skills**, **swarm intelligence architecture**, **14 AI brain modules**, and self-learning capabilities. It plans, executes, learns, and **thinks like a real penetration tester** — no manual configuration needed.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Pull-2496ED.svg?logo=docker)](https://hub.docker.com/r/iamaworker-github/argus)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-181717.svg?logo=github)](https://github.com/iamaworker-github/argus)
[![Agents](https://img.shields.io/badge/Agents-60%2B-8957e5)](https://github.com/iamaworker-github/argus)
[![Skills](https://img.shields.io/badge/Skills-150%2B-1f6feb)](https://github.com/iamaworker-github/argus)

---

## Quick Install

### One-line (Linux/macOS)
```bash
curl -fsSL https://raw.githubusercontent.com/iamaworker-github/argus/main/install.sh | bash
```

### Docker
```bash
# Main Argus platform
docker run -d --name argus -p 8484:8484 \
  -e OPENAI_API_KEY="sk-..." \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  iamaworker-github/argus:latest

# CTF solver sandbox (isolated challenge environment)
docker run -d --name argus-ctf-sandbox \
  iamaworker-github/argus-ctf-sandbox:latest
```

---

## Architecture

Argus has **two parallel execution modes** that can be used independently or together:

### 1. 🐝 Swarm Mode (Stigmergic Blackboard)
```
TARGET_REGISTERED ──► recon agent wakes (pheromone: 0.8)
       │
       ▼ writes SUBDOMAIN (pheromone: 0.8, half-life: 600s)
SUBDOMAIN ──► tech_detect agent wakes (threshold: 0.3)
       │
       ▼ writes TECHNOLOGY (pheromone: 0.7)
TECHNOLOGY ──► nuclei/CVE agent wakes (threshold: 0.4)
       │
       ▼ writes VULNERABILITY (pheromone: 0.9)
VULNERABILITY ──► exploit agent wakes (threshold: 0.6)
       │
       ▼ writes EXPLOIT_RESULT
EXPLOIT_RESULT ──► chain agent wakes (threshold: 0.5)
       │
       ▼ writes CAMPAIGN_COMPLETE ──► report agent (threshold: 0.9)
```

- **No central planner** — agents coordinate via shared blackboard with pheromone weights
- **Pheromone decay** — `w(t) = base × 2^(-t/half_life)` — stale paths die naturally
- **Emergent attack chains** — order emerges from state, not from prescribed phases
- **Exploration bias** — `--bias high` = aggressive, `--bias low` = conservative

### 2. 🧠 AI Executor Mode (Think → Decide → Execute)
```
Phase 0: AI Planning ─── TargetProfiler + RL scan strategy
Phase 1: Reconnaissance ─── AI-selected tools + MCTS prioritization
Phase 2: Enumeration ─── Smart brute-force + port service enum
Phase 3: Vulnerability ─── AI agent selection + ReAct loop
Phase 3.5: ReAct Loop ─── Meta-cognition + self-healing exploits
Phase 3.6: AI EXECUTOR ─── LLM brain: think→decide→execute→observe
Phase 4: AI Analysis ─── PoC validation + debate + chain discovery
Phase 5: Exploitation ─── AI chaining + failover + tool generation
Phase 6: Reporting ─── Cross-target intel + AI reports
```

---

## Features

### 🐝 Swarm Intelligence
| Feature | Description |
|---------|-------------|
| **Stigmergic Blackboard** | Shared knowledge store with pheromone weights + time decay |
| **Trigger Predicates** | Each agent has a trigger rule — wakes when relevant state appears |
| **Emergent Scheduler** | No central planner — dispatching emerges from blackboard state |
| **Exploration Bias** | `--bias low|med|high` — controls aggression vs thoroughness |
| **Playbook Engine** | YAML playbooks: bug-bounty, external-asm, ci-cd, ctf-solver |

### 🧠 14 AI Brain Modules
| Module | What it does |
|--------|-------------|
| **AI Executor** | Primary decision loop — LLM thinks, decides, commands agents |
| **Self-Reflection** | Deep root-cause analysis after failures |
| **Prompt Evolution** | Auto-improves scan prompts from past failures |
| **Reinforcement Learning** | Q-learning (epsilon-greedy) — learns optimal scan strategies |
| **Cross-Target Intel** | Learns patterns across targets — "X worked on nginx+php before" |
| **Target Profiler** | Per-domain fingerprint with cross-session learning |
| **Vuln Chaining AI** | LLM discovers attack chains from low/medium findings |
| **Debate Engine** | Multi-agent cross-validation of findings |
| **Self-Healing Exploits** | Auto-mutates payloads on failure (WAF bypass) |
| **Tool Generator** | LLM generates + verifies new Python tools on-the-fly |
| **Failover Engine** | Plan A fails → LLM generates Plans B/C/D |
| **ReAct v2** | Chain-of-thought + real-time tool execution |
| **AI False Positive Verifier** | LLM cross-validates findings against request/response |
| **AI Report Generator** | Executive + technical summaries in natural language |

### 🔧 Agent Arsenal (60+ Agents)
| Category | Agents |
|----------|--------|
| **Core Web** | SQLi, XSS, SSRF, IDOR, SSTI, XXE, CORS, Command Injection, Open Redirect, NoSQLi, Host Header, Rate Limit, LFI, Prototype Pollution |
| **Auth & Identity** | JWT Attack, Authentication, OAuth Hunter, SAML Attack, Session Management |
| **Cloud & Infra** | Cloud Security, Container Escape, Kubernetes, WAF Detection/Bypass, Nuclei |
| **Bug Bounty** | VDP Discovery, Android APK Hacker, Web3 Auditor, CVE Exploiter, JS Secrets, Function-Wise Hunter, Info Disclosure Hunter, LLM Recon Chain, Race Condition Hunter |
| **Bug Bounty Pipeline** | Pipeline Orchestrator (7-phase), Two-Eye Approach, Cache Poisoning, CRLF Injection, Exploit Chain Builder (A→B→C) |
| **CTF Solving** | CTF Solver, Advanced CTF Solver (11 categories, 100+ techniques), Racing CTF Agent (multi-model) |
| **OSINT** | OSINT Collector, Social Intel, Leak Intel, DNS Intel, Google Dork, Crypto OSINT |
| **Enterprise** | IoT Security, Mobile Pentest, API Pentest, LLM Red Team, AI Security |
| **Infrastructure** | Recon Agent, Smart Brute Force, Port Scanner, Medusa, PoC Validator, Remediation |

### 🎯 Skills Library (150+ Skills)
- **Vaidik Pandya Methodologies**: VDP hunter, Android APK, Web3 smart contract, JS secrets, function-wise hunting, CVE exploitation, info disclosure, LLM recon automation, race conditions, subfinder mastery
- **2026 Bug Bounty Pipeline**: Full 7-phase pipeline, Two-Eye Approach, cache poisoning, CRLF injection
- **Hunting Skills**: RCE (1,135 lines), IDOR (969 lines), XSS (968 lines), OAuth (770 lines), LLM/AI (930 lines)
- **CTF Skills**: 11 categories (pwn, rev, crypto, forensics, web, osint, stego, ai_ml, malware, blockchain, misc)
- **Pentesting**: Account takeover, SSRF, SQLi, XSS, JWT, CSRF, XXE, deserialization, file upload, business logic, GraphQL, race conditions, web3, mobile, cloud, AD, IoT
- **Methodology**: Recon methodology, hunting methodology, report writing, SAST methodology, triage validation, vulnerability classes

### 🌐 MCP Server
Connect Claude Desktop, Cursor, VS Code Copilot, or any MCP-compatible tool directly to Argus:
```bash
argus mcp serve
```

**MCP Tools available:**
| Tool | Description |
|------|-------------|
| `run_scan` | Start scan on target |
| `get_status` | Check scan progress |
| `bounty_search_programs` | Search HackerOne/Bugcrowd programs |
| `bounty_submit_report` | Draft/submit bug bounty reports |
| **`writeup_search`** | Semantic search over prior art writeups (28 vuln classes) |
| **`writeup_techniques`** | Get exploitation techniques by vuln class |
| **`writeup_payloads`** | Get payload samples by vuln class |
| `health_check` | System health and diagnostics |

Then in Claude Desktop config:
```json
{
  "mcpServers": {
    "argus": {
      "command": "argus",
      "args": ["mcp", "serve"]
    }
  }
}
```

### 📊 Web Dashboard
Real-time scan monitoring with live WebSocket updates, swarm visualization, agent activity feed, and session persistence.

---

## CLI Commands

```bash
# Traditional pentest
argus strix --target https://example.com -m deep

# Swarm mode
argus swarm --target example.com --playbook bug-bounty --bias high

# Bug bounty full pipeline (7-phase)
argus pipeline --target https://example.com

# List playbooks
argus playbook list

# Run a specific playbook
argus playbook run bug-bounty --target example.com

# MCP server for Claude/Cursor
argus mcp serve

# Web dashboard
argus web --host 0.0.0.0 --port 8484
```

### Swarm Playbooks
| Playbook | Description | Budget |
|----------|-------------|--------|
| `bug-bounty` | Fast recon → high-value vulns | 30 min |
| `external-asm` | Attack surface management | 60 min |
| `ci-cd` | Fast feedback for dev teams | 10 min |
| `ctf-solver` | Aggressive CTF scanning | 120 min |

---

## Scan Modes

| Mode | Duration | Description |
|------|----------|-------------|
| `quick` | 5-15 min | Surface scan — CI/CD gate, low-hanging fruit |
| `standard` | 30-60 min | Standard depth — bug bounty triage |
| `deep` | 1-4 hrs | Full coverage — pentest engagement |
| `whitebox` | varies | Source-sink analysis — code review |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | One required | OpenAI / Azure OpenAI |
| `ANTHROPIC_API_KEY` | One required | Anthropic Claude |
| `GOOGLE_API_KEY` | Optional | Google Gemini |
| `GROQ_API_KEY` | Optional | Groq (fast inference) |
| `DEEPSEEK_API_KEY` | Optional | DeepSeek models |
| `GITHUB_TOKEN` | Optional | For auto PR creation |
| `CTF_SANDBOX_IMAGE` | Optional | CTF sandbox Docker image name |
| `CTF_SANDBOX_TIMEOUT` | Optional | CTF solver timeout (default: 1800s) |

Argus uses **LiteLLM** — any provider supported by LiteLLM works automatically.

---

## Docker Images

| Image | Pull Command | Description |
|-------|-------------|-------------|
| **Argus Platform** | `docker pull iamaworker-github/argus:latest` | Full platform: 60+ agents, web dashboard, MCP, all tools |
| **CTF Sandbox** | `docker pull iamaworker-github/argus-ctf-sandbox:latest` | Isolated CTF solver env: pwntools, radare2, volatility3, angr, z3 |

**Argus Platform** includes: Python 3.11, 60+ agents, 150+ skills, 14 AI modules, swarm architecture, MCP server, web dashboard, nmap, pd-httpx, nuclei, naabu, katana, gau, waybackurls.

**CTF Sandbox** includes: pwntools, radare2, GDB, volatility3, foremost, steghide, zsteg, binwalk, ROPgadget, angr, z3-solver, pycryptodome, capstone, unicorn.

---

## License

Apache 2.0 License — see [LICENSE](LICENSE).

---

*Built by [iamaworker-github](https://github.com/iamaworker-github) — See Everything. Miss Nothing.*
