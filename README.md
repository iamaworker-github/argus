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
> AI-powered autonomous security testing platform with multi-agent architecture
> 
> ✨ **NEW**: Now featuring full **Strix-compatible interface** — use `argus strix -t <target>` with all Strix CLI flags, scan modes (quick/standard/deep), skills system, and AI-driven pentesting!

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Beta-yellow.svg)]()

## 🚀 Overview

**Argus** is an AI-powered security testing platform that deploys autonomous agents to identify and validate application vulnerabilities. Named after the all-seeing giant from Greek mythology, Argus uses multiple specialized AI agents working in parallel to discover security flaws with validated proof-of-concepts.

### Key Features

- 🤖 **Multi-Agent Architecture**: Specialized agents for different attack vectors
- 🧠 **AI-Powered Analysis**: LLM integration (OpenAI/Anthropic) for intelligent testing
- 🔧 **Complete Security Toolkit**: HTTP proxy, browser automation, shell executor, Python runtime
- ⚡ **Parallel Execution**: Run multiple agents concurrently for faster results
- 🎯 **Validated Findings**: Proof-of-concept generation with Strix-style false positive reduction
- 🖥️ **Beautiful TUI**: Professional terminal interface with real-time monitoring
- 🐳 **Docker Support**: Isolated sandbox environment for safe testing
- 🔄 **Strix-Compatible**: Full Strix CLI interface with scan modes, skills system, and AI-driven planning
- 📚 **Skills System**: 18+ specialized knowledge packages for deep vulnerability expertise
- 🎚️ **Scan Depth**: Quick (minutes), Standard (30min-1hr), Deep (1-4hrs) modes

## 🎯 What Argus Does

Argus automatically detects:

- **Injection Flaws**: SQL, NoSQL, Command Injection
- **Cross-Site Scripting (XSS)**: Reflected, Stored, DOM-based
- **Server-Side Request Forgery (SSRF)**: Internal network access
- **Authentication Issues**: Weak credentials, session management
- **Access Control**: IDOR, privilege escalation
- **Information Disclosure**: Sensitive endpoints, exposed data

## 📋 Requirements

- **Python**: 3.8 or higher
- **Docker**: For sandboxed execution (optional but recommended)
- **API Keys**: OpenAI or Anthropic (for AI features)

## 🚀 Quick Start

### Installation

**One-liner (Linux/macOS):**
```bash
curl -fsSL https://raw.githubusercontent.com/iamaworker-github/argus/main/scripts/install.sh | bash
```

**Or clone manually:**
```bash
git clone https://github.com/iamaworker-github/argus.git
cd argus
bash scripts/install.sh --full
```

### Claude Code Agents (Optional)

Argus includes **43 specialized AI agents** for Claude Code that turn it into a multi-agent cybersecurity assistant:

```bash
# Install agents globally (available in all Claude Code sessions)
bash scripts/install.sh --global

# Or one-liner:
curl -fsSL https://raw.githubusercontent.com/iamaworker-github/argus/main/scripts/install.sh | bash -s -- --global
```

Agents include: `web-hunter`, `recon-advisor`, `vuln-scanner`, `exploit-guide`, `ssrf-hunter`, `cloud-security`, `ad-attacker`, and 36 more — covering recon, web app, cloud, AD, mobile, social engineering, forensics, and reporting.

### Basic Usage

**Strix-Style CLI (Pentest Mode - Recommended):**
```bash
# Basic scan (deep mode, AI-driven)
argus strix -t https://example.com

# Quick scan for CI/CD
argus strix -t https://example.com -m quick -n

# Standard scan with custom focus
argus strix -t https://example.com -m standard --instruction "Focus on auth bypass and IDOR"

# Deep scan with remediation suggestions
argus strix -t ./my-app --remediation

# With instruction file
argus strix -t https://api.example.com --instruction-file ./pentest-instructions.md
```

**Legacy CLI:**
```bash
# Basic scan
argus scan example.com

# Parallel execution
argus scan example.com --parallel

# Verbose output
argus scan example.com -v

# Custom output directory
argus scan example.com -o ./my_results
```

**TUI Mode (Interactive):**
```bash
# Launch Strix-inspired UI (default)
argus tui example.com

# Or explicitly
argus tui example.com --strix

# Use legacy professional UI
argus tui example.com --professional
```

> 📖 See [STRIX_UI_GUIDE.md](STRIX_UI_GUIDE.md) for complete UI documentation

### Configuration (Strix-Style)

Argus supports Strix-compatible environment variables:

```bash
# Required for AI features
export STRIX_LLM="openai/gpt-5.4"
export LLM_API_KEY="your-api-key"

# Or use legacy argus config
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."

# Optional features
export PERPLEXITY_API_KEY="pplx-..."  # Web search for OSINT
export STRIX_REASONING_EFFORT="high"  # none/minimal/low/medium/high/xhigh
export LLM_TIMEOUT="300"              # Request timeout in seconds
```

Config file at `~/.argus/cli-config.json` (auto-loaded):

```json
{
  "env": {
    "STRIX_LLM": "openai/gpt-5.4",
    "LLM_API_KEY": "sk-..."
  }
}
```

**Docker Mode (Recommended):**
```bash
# Build image
docker build -t argus .

# Run scan
docker run -it --rm \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/results:/app/argus_results \
  argus scan example.com --parallel
```

## 🏗️ Architecture

### Project Structure

```
argus/
├── argus/
│   ├── core/              # Core modules
│   │   ├── config.py      # Configuration management
│   │   └── logger.py      # Logging system
│   ├── agents/            # AI security agents
│   │   ├── base_agent.py  # Base agent class
│   │   ├── orchestrator.py # Agent coordination
│   │   ├── sql_injection_agent.py
│   │   ├── xss_agent.py
│   │   ├── ssrf_agent.py
│   │   └── recon_agent.py
│   ├── toolkit/           # Security toolkit
│   │   ├── browser.py     # Browser automation
│   │   ├── http_proxy.py  # HTTP proxy
│   │   ├── shell.py       # Shell executor
│   │   └── python_runtime.py # Python sandbox
│   ├── ui/                # User interface
│   │   └── app.py         # Textual TUI
│   └── cli.py             # CLI entry point
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Example scripts
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
└── setup.py              # Package setup
```

### Multi-Agent System

Argus uses a **Graph of Agents** architecture:

1. **Recon Agent**: Information gathering, subdomain discovery, technology detection
2. **SQL Injection Agent**: Tests for SQL injection vulnerabilities
3. **XSS Agent**: Detects cross-site scripting flaws
4. **SSRF Agent**: Identifies server-side request forgery

Agents run in parallel and share findings through the orchestrator.

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# AI Provider (choose one or both)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Default AI Model
AI_MODEL=gpt-4-turbo-preview

# Scanning Configuration
MAX_CONCURRENT_AGENTS=5
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# Browser Automation
HEADLESS_BROWSER=true
BROWSER_TIMEOUT=30000

# Output
OUTPUT_DIR=./argus_results
VERBOSE=false
DEBUG=false
```

### Programmatic Usage

```python
from argus.agents.orchestrator import AgentOrchestrator
from argus.core.config import Config, set_config

# Configure
config = Config(verbose=True)
set_config(config)

# Create orchestrator
orchestrator = AgentOrchestrator("example.com")
orchestrator.add_default_agents()

# Run scan
result = await orchestrator.run_parallel()

# Access findings
for finding in result.all_findings:
    print(f"{finding.severity}: {finding.title}")
```

## 📊 Output

Argus generates:

- **JSON Report**: Complete scan results with all findings
- **Structured Findings**: Severity, category, evidence, PoC, remediation
- **Real-time Logs**: Detailed execution logs

Example finding:

```json
{
  "title": "SQL Injection in GET parameter",
  "severity": "critical",
  "category": "injection",
  "evidence": "Response contains SQL error",
  "proof_of_concept": "GET http://example.com?id=' OR '1'='1",
  "remediation": "Use parameterized queries",
  "confidence": 0.9,
  "agent_name": "SQL Injection Agent"
}
```

## 🐳 Docker Usage

### Build Image

```bash
docker build -t argus .
```

### Run Scan

```bash
docker run -it --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/results:/app/argus_results \
  argus scan target.com --parallel
```

### Docker Compose

```bash
docker-compose up
```

## 🛡️ Security & Ethics

**⚠️ IMPORTANT: Only use Argus on systems you own or have explicit permission to test!**

### Authorized Use Cases

- ✅ Bug bounty programs (with authorization)
- ✅ Penetration testing (with contract)
- ✅ Security assessments (authorized)
- ✅ Your own applications
- ✅ Educational purposes (on test environments)

### Prohibited Use

- ❌ Unauthorized scanning
- ❌ Malicious intent
- ❌ Without explicit permission

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📝 License

Apache License 2.0 - See [LICENSE](LICENSE) file for details.

## 🙏 Credits

**Built with:**
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [Playwright](https://playwright.dev/) - Browser automation
- [OpenAI](https://openai.com/) / [Anthropic](https://anthropic.com/) - AI models

**Inspired by:**
- [Strix](https://github.com/usestrix/strix) - Security testing concepts

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/iamaworker-github/argus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iamaworker-github/argus/discussions)

## ⭐ Star History

If you find Argus useful, please star the repository!

---

**Made with ❤️ for the security community**

*Remember: Always obtain proper authorization before testing any systems you don't own.*
