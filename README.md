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
> Argus is an AI-powered autonomous security testing platform with **50+ specialized agents**, **swarm intelligence architecture**, **14 AI brain modules**, and self-learning capabilities. It plans, executes, learns, and **thinks like a real penetration tester** — no manual configuration needed.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Pull-2496ED.svg?logo=docker)](https://hub.docker.com/r/iamaworker135/argus)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-181717.svg?logo=github)](https://github.com/iamaworker-github/argus)

---

## Quick Install

### One-line (Linux/macOS)
```bash
curl -fsSL https://raw.githubusercontent.com/iamaworker-github/argus/main/install.sh | bash
```

### Docker
```bash
docker run -d --name argus -p 8484:8484 \
  -e OPENAI_API_KEY="sk-..." \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  iamaworker135/argus:latest-ai
```

---

## Architecture

Argus has **two parallel execution modes** that can be used independently or together:

### 1. 🐝 Swarm Mode (NEW — Stigmergic Blackboard)
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

### 🐝 Swarm Intelligence (New)
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

### 🔧 Agent Arsenal
- **50+ Specialized Agents** — SQLi, XSS, SSRF, JWT, IDOR, LFI, RCE, XXE, SSTI, CORS, Open Redirect, NoSQLi, Host Header, Rate Limit, WAF Detection, Nuclei, Smart Brute Force, and 40+ more
- **MCTS Attack Planning** — Monte Carlo Tree Search prioritizes attack paths
- **Cross-Agent Reactions** — Agent A's findings trigger Agent B automatically
- **Auto Remediation PR** — LLM generates fixes + creates GitHub PRs

### 🌐 MCP Server (New)
Connect Claude Desktop, Cursor, or any MCP-compatible tool directly to Argus:
```bash
argus mcp serve
```
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

# Swarm mode (NEW)
argus swarm --target example.com --playbook bug-bounty --bias high

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

Argus uses **LiteLLM** — any provider supported by LiteLLM works automatically.

---

## Docker Image

**Pull:** `docker pull iamaworker135/argus:latest-ai`

Includes: Python 3.11, 50+ agents, 14 AI modules, swarm architecture, MCP server, web dashboard, nmap, pd-httpx, nuclei, naabu, katana, gau, waybackurls, and all dependencies.

---

## License

Apache 2.0 License — see [LICENSE](LICENSE).

---

*Built by [iamaworker-github](https://github.com/iamaworker-github) — See Everything. Miss Nothing.*
