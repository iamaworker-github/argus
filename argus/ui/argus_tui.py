"""
ARGUS v0.8.3 — Autonomous AI Cybersecurity Cockpit TUI
Pixel-perfect Textual implementation matching STRIX UI/UX spec
"""

import asyncio
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Optional, Any, Callable
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll, HorizontalScroll
from textual.widgets import Static, Input, Label, Button, ProgressBar, DataTable, Header, Footer, RichLog
from textual.reactive import reactive
from textual import events
from textual.binding import Binding
from textual.widget import Widget
from textual.screen import ModalScreen
from textual.message import Message
from rich.text import Text
from rich.style import Style
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.columns import Columns
from rich.progress_bar import ProgressBar as RichProgressBar
from rich.console import RenderableType
from rich.align import Align
from rich.spinner import Spinner
from rich_pixels import Pixels

# ============================================================
# INTEGRATION HOOK: Replace with your actual ARGUS backend
# ============================================================
class ArgusBackend:
    """Mock backend for standalone demo mode.
    Replace all method bodies with real ARGUS tool integrations.
    """
    def __init__(self):
        self._start_time = time.time()
        self._agents = [
            {"name": "Subdomain Enum", "status": "running", "type": "recon"},
            {"name": "Port Scanner", "status": "running", "type": "recon"},
            {"name": "Content Discovery", "status": "running", "type": "recon"},
            {"name": "Tech Analysis", "status": "queued", "type": "analysis"},
        ]
        self._findings = [
            {"title": "Open port 443", "severity": "info", "target": "evil.com", "time": "06:11:15"},
            {"title": "Open port 80", "severity": "info", "target": "evil.com", "time": "06:11:16"},
            {"title": "Nginx 1.24.0 detected", "severity": "low", "target": "evil.com", "time": "06:11:22"},
            {"title": "PHP 8.1.2 detected", "severity": "medium", "target": "evil.com", "time": "06:11:35"},
            {"title": "SQL injection potential in login", "severity": "high", "target": "evil.com", "time": "06:12:01"},
        ]
        self._activity_feed = [
            ("06:11:02", "Subdomain Enum", "Discovered 23 subdomains"),
            ("06:11:15", "Port Scanner", "Found 4 open ports"),
            ("06:11:22", "Content Discov", "Started web crawling on 4 targets"),
            ("06:11:35", "Tech Analysis", "Detecting technologies and frameworks"),
            ("06:11:42", "Orchestrator", "Updated attack graph with 8 new nodes"),
        ]
        self._subdomains = ["api.evil.com", "client.evil.com", "assets.evil.com", "admin.evil.com"]
        self._technologies = [
            ("PHP 8.1.2", 45),
            ("Nginx", 30),
            ("Cloudflare", 15),
            ("jQuery", 10),
        ]
        self._recent_disco = [
            ("api.evil.com", "06:11:02"),
            ("client.evil.com", "06:11:03"),
            ("assets.evil.com", "06:11:04"),
            ("MySQL 8.0.32", "06:11:38"),
            ("Redis 6.2.11", "06:11:39"),
        ]
        self._pipeline_stages = [
            {"name": "Reconnaissance", "completed": 4, "total": 4, "status": "complete"},
            {"name": "Enumeration", "completed": 3, "total": 4, "status": "current"},
            {"name": "Analysis", "completed": 0, "total": 3, "status": "pending"},
            {"name": "Vulnerability", "completed": 0, "total": 4, "status": "pending"},
            {"name": "Exploitation", "completed": 0, "total": 2, "status": "pending"},
            {"name": "Reporting", "completed": 0, "total": 2, "status": "pending"},
        ]
        self._findings_by_severity = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        self._commands_executed = 47
        self._data_collected = 12.4
        self._findings_count = 19
        self._vulnerabilities = 0

    def get_agents(self) -> list[dict]:
        return self._agents

    def get_findings(self) -> list[dict]:
        return self._findings

    def get_system_stats(self) -> dict:
        uptime_secs = time.time() - self._start_time
        return {
            "cpu": random.randint(15, 45),
            "mem": random.randint(30, 70),
            "net": random.randint(5, 25),
            "tokens_used": 1.2,
            "tokens_total": 2.0,
            "credits": 4872,
            "uptime": uptime_secs,
            "commands": self._commands_executed,
            "data_collected": self._data_collected,
            "findings": self._findings_count,
            "vulnerabilities": self._vulnerabilities,
        }

    def run_command(self, cmd: str) -> str:
        return f"[{datetime.now().strftime('%H:%M:%S')}] Executing: {cmd}"

    def get_activity_feed(self) -> list[tuple]:
        return self._activity_feed

    def get_pipeline_stages(self) -> list[dict]:
        return self._pipeline_stages

    def get_subdomains(self) -> list[str]:
        return self._subdomains

    def get_technologies(self) -> list[tuple]:
        return self._technologies

    def get_recent_discoveries(self) -> list[tuple]:
        return self._recent_disco

    def get_target_info(self) -> dict:
        return {
            "target": "evil.com",
            "ip": "93.184.216.34",
            "open_ports": 4,
            "subdomains": 3,
            "technologies": 7,
            "risk": "Medium",
        }

    def get_attack_graph_nodes(self) -> list[dict]:
        return [
            {"id": 0, "label": "evil.com", "type": "host", "children": [1, 2, 3]},
            {"id": 1, "label": "api.evil.com", "type": "host", "children": [4]},
            {"id": 2, "label": "client.evil.com", "type": "host", "children": [5]},
            {"id": 3, "label": "assets.evil.com", "type": "host", "children": [6]},
            {"id": 4, "label": "Auth API", "type": "service", "children": [8]},
            {"id": 5, "label": "Web App PHP", "type": "app", "children": [9, 10]},
            {"id": 6, "label": "CDN CF", "type": "service", "children": []},
            {"id": 8, "label": "Login", "type": "endpoint", "children": []},
            {"id": 9, "label": "MySQL", "type": "datastore", "children": []},
            {"id": 10, "label": "Redis", "type": "datastore", "children": []},
        ]

    def stream_agent_output(self, agent_name: str) -> list[str]:
        outputs = {
            "Subdomain Enum": [
                "subfinder -d evil.com -all -o /tmp/subdomains.txt",
                "Found 23 subdomains from 4 sources",
                "DNS brute-force completed: 1423 queries",
                "Results written to: /workspace/results/subdomains.txt",
            ],
            "Port Scanner": [
                "naabu -host evil.com -p 22,80,443,8080,8443 -rate 1000",
                "evil.com:443 open",
                "evil.com:80 open",
                "evil.com:8443 open",
                "evil.com:22 open",
                "nmap -n -Pn -p 22,80,443,8443 -sV -sC evil.com",
                "Starting Nmap at scan initiation...",
                "Nmap scan completed: 4 open ports",
                "Service detection and version enumeration in progress...",
                "Writing results to: /workspace/results/portscan.txt",
            ],
            "Content Discovery": [
                "ffuf -u https://evil.com/FUZZ -w /wordlists/common.txt -t 50",
                "Found: /admin (301)",
                "Found: /api (200)",
                "Found: /login (200)",
                "Found: /assets (301)",
                "Crawling 4 targets for endpoint discovery",
            ],
            "Tech Analysis": [
                "wappalyzer https://evil.com",
                "Detecting technologies and frameworks...",
                "PHP 8.1.2 confirmed",
                "Nginx 1.24.0 confirmed",
                "Cloudflare CDN detected",
                "jQuery 3.6.0 detected",
            ],
        }
        return outputs.get(agent_name, [f"No output for {agent_name}"])


# ============================================================
# DEMO DATA GENERATOR
# ============================================================
class DemoDataGenerator:
    """Generates realistic-looking demo data for standalone testing"""
    def __init__(self, backend: ArgusBackend):
        self.backend = backend
        self._log_lines: dict[str, list[str]] = {}
        self._current_line: dict[str, int] = {}

    def get_next_log_line(self, agent_name: str) -> str | None:
        if agent_name not in self._log_lines:
            self._log_lines[agent_name] = self.backend.stream_agent_output(agent_name)
            self._current_line[agent_name] = 0
        idx = self._current_line.get(agent_name, 0)
        if idx < len(self._log_lines[agent_name]):
            line = self._log_lines[agent_name][idx]
            self._current_line[agent_name] = idx + 1
            return line
        return None


# ============================================================
# WIDGETS
# ============================================================

class Pulse(Static):
    """Pulsing live indicator"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._on = True
        self._update_content()

    def on_mount(self) -> None:
        self.set_interval(1, self._toggle)

    def _toggle(self) -> None:
        self._on = not self._on
        self._update_content()

    def _update_content(self) -> None:
        t = Text()
        if self._on:
            t.append("● LIVE", style=Style(color="#00ff41", bold=True))
        else:
            t.append("○ LIVE", style=Style(color="#1a3a1a"))
        self.update(t)


class LiveTimer(Static):
    """Live updating HH:MM:SS clock"""
    def on_mount(self) -> None:
        self.set_interval(1, self._tick)

    def _tick(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self.update(Text(now, style=Style(color="#c8ffc8")))


class AgentStatusDot(Static):
    """Colored status dot for agent list"""
    def __init__(self, agent_name: str = "", status: str = "queued", **kwargs):
        super().__init__(**kwargs)
        self.agent_name = agent_name
        self._status = status
        self._render_status()

    def set_status(self, status: str) -> None:
        self._status = status
        self._render_status()

    def _render_status(self) -> None:
        t = Text()
        if self._status == "running":
            t.append("● Running", style=Style(color="#00ff41", bold=True))
            t.append("  ⏳", style=Style(color="#4a7a4a"))
        elif self._status == "queued":
            t.append("● Queued", style=Style(color="#ffb300", bold=True))
        else:
            t.append("● Idle", style=Style(color="#4a7a4a"))
        self.update(t)


# ============================================================
# HEADER BAR
# ============================================================
class ArgusHeader(Horizontal):
    """Top header bar — full width, 1 row"""
    def compose(self) -> ComposeResult:
        with Horizontal(id="header-left"):
            yield Static("ARGUS", id="brand-name")
            yield Static("v0.8.3", id="version-badge")
            yield Static("AUTONOMOUS AI CYBERSECURITY COCKPIT", id="header-subtitle")
        with Horizontal(id="header-right"):
            yield Static("OPERATION:", id="op-label")
            yield Static("PENTEST", id="op-value")
            yield Static("TARGET:", id="target-label")
            yield Static("evil.com", id="target-value")
            yield Static("SESSION:", id="session-label")
            yield Static("SES-8A3F", id="session-value")
            yield Static("TIME:", id="time-label")
            yield LiveTimer(id="live-timer")
            yield Pulse(id="live-pulse")


# ============================================================
# BOTTOM BAR
# ============================================================
class ArgusFooter(Horizontal):
    """Bottom input bar — full width, 1 row"""
    def compose(self) -> ComposeResult:
        yield Static("strix@cockpit:~# ", id="prompt")
        yield Input(placeholder="Type command or ask AI...", id="command-input")
        yield Static("? Help", id="help-hint")
        yield Static("Tab Complete", id="tab-hint")
        yield Static("Ctrl+K Commands", id="cmd-hint")
        yield Static("Ctrl+D Exit", id="exit-hint")


# ============================================================
# LEFT PANEL
# ============================================================
class EagleLogo(Widget):
    """Rich pixel art eagle logo using rich-pixels"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pixels = Pixels.from_image_path('/root/references/argus_eagle.png')

    def render(self) -> RenderableType:
        return self._pixels


class AgentStatusCard(Vertical):
    """Section 1: Agent Status Card with eagle pixel art"""
    def compose(self) -> ComposeResult:
        yield EagleLogo(id="eagle-logo")
        yield Static("STATUS", id="status-label")
        yield Static("EXECUTING", id="status-value")
        yield Static("MODE: Autonomous", id="mode-value")
        yield Static("RISK PROFILE: Balanced", id="risk-value")
        yield Static("MAX PARALLEL: 4 agents", id="parallel-value")
        yield Static("SAFE MODE: ON", id="safe-mode-value")

class AgentList(Vertical):
    """Section 2: Agents list with status"""
    def compose(self) -> ComposeResult:
        yield Static("AGENTS [4/4]", id="agents-title")
        # These will be dynamically updated
        yield Static("⊗ Subdomain Enum", id="agent-0-name", classes="agent-row selected")
        yield AgentStatusDot(agent_name="Subdomain Enum", status="running", id="agent-0-status")
        yield Static("⊗ Port Scanner", id="agent-1-name", classes="agent-row")
        yield AgentStatusDot(agent_name="Port Scanner", status="running", id="agent-1-status")
        yield Static("⊗ Content Discov", id="agent-2-name", classes="agent-row")
        yield AgentStatusDot(agent_name="Content Discovery", status="running", id="agent-2-status")
        yield Static("⊗ Tech Analysis", id="agent-3-name", classes="agent-row")
        yield AgentStatusDot(agent_name="Tech Analysis", status="queued", id="agent-3-status")
        with Horizontal(id="agent-actions"):
            yield Static("+ New Agent", id="new-agent-btn")
            yield Static("Launch", id="launch-btn")
        with Horizontal(id="agent-tools"):
            yield Static("⚙ Orchestrator  Active", id="orchestrator-status")
        with Horizontal(id="agent-resources"):
            yield Static("◎ Memory         87%", id="memory-status")
            yield Static("◈ Knowledge Base  Synced", id="kb-status")

class SysHealthBar(Widget):
    """Single system health bar line"""
    def __init__(self, label: str, value: int, color: str = "#00ff41", **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._value = value
        self._color = color

    def update_value(self, value: int) -> None:
        self._value = value
        self.refresh()

    def render(self) -> RenderableType:
        bar_len = 12
        filled = int(bar_len * self._value / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        t = Text()
        t.append(f"{self._label} ", style=Style(color="#4a7a4a"))
        t.append(bar, style=Style(color=self._color))
        t.append(f" {self._value:>2}%", style=Style(color="#c8ffc8"))
        return Panel(t)

class SysHealthBars(Vertical):
    """Section 3: System health progress bars"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cpu = SysHealthBar("CPU", 23, "#00ff41", id="cpu-bar")
        self._mem = SysHealthBar("MEM", 41, "#00ff41", id="mem-bar")
        self._net = SysHealthBar("NET", 12, "#ffb300", id="net-bar")

    def compose(self) -> ComposeResult:
        yield Static("SYSTEM HEALTH", id="health-title")
        yield self._cpu
        yield self._mem
        yield self._net
        yield Static("TOKENS  1.2M / 2.0M", id="tokens-line")
        yield Static("CREDITS  4,872", id="credits-line")
        yield Static("UPTIME  00:00:00", id="uptime-line")

    def update(self, stats: dict) -> None:
        self._cpu.update_value(stats.get("cpu", 0))
        self._mem.update_value(stats.get("mem", 0))
        self._net.update_value(stats.get("net", 0))
        tokens = stats.get("tokens_used", 0)
        tokens_total = stats.get("tokens_total", 1)
        credits = stats.get("credits", 0)
        uptime = stats.get("uptime", 0)
        uptime_str = str(timedelta(seconds=int(uptime)))
        self.query_one("#tokens-line", Static).update(f"TOKENS  {tokens:.1f}M / {tokens_total:.1f}M")
        self.query_one("#credits-line", Static).update(f"CREDITS  {credits:,}")
        self.query_one("#uptime-line", Static).update(f"UPTIME  {uptime_str}")


class LeftPanel(VerticalScroll):
    """Left panel — Agents + System Health (20%)"""
    def compose(self) -> ComposeResult:
        yield AgentStatusCard(id="agent-status-card")
        yield AgentList(id="agent-list")
        yield SysHealthBars(id="sys-health-bars")


# ============================================================
# CENTER PANEL
# ============================================================
class PipelineStage(Widget):
    """Single pipeline stage indicator"""
    def __init__(self, stage_name: str, completed: int, total: int, status: str, **kwargs):
        super().__init__(**kwargs)
        self._stage_name = stage_name
        self._stage_completed = completed
        self._stage_total = total
        self._stage_status = status

    def render(self) -> RenderableType:
        style_map = {
            "complete": Style(color="#00ff41", bold=True),
            "current": Style(color="#ffb300", bold=True),
            "pending": Style(color="#2a4a2a"),
        }
        style = style_map.get(self._stage_status, style_map["pending"])
        t = Text()
        t.append(f"{self._stage_name}({self._stage_completed}/{self._stage_total})", style=style)
        return Panel(t)

class PipelineStepper(HorizontalScroll):
    """Horizontal pipeline stepper with stages"""
    def compose(self) -> ComposeResult:
        yield PipelineStage("Reconnaissance", 4, 4, "complete", id="pipe-0")
        yield Static(" ─────●───── ", id="connector-0")
        yield PipelineStage("Enumeration", 3, 4, "current", id="pipe-1")
        yield Static(" ─────●───── ", id="connector-1")
        yield PipelineStage("Analysis", 0, 3, "pending", id="pipe-2")
        yield Static(" ─────●───── ", id="connector-2")
        yield PipelineStage("Vulnerability", 0, 4, "pending", id="pipe-3")
        yield Static(" ─────●───── ", id="connector-3")
        yield PipelineStage("Exploitation", 0, 2, "pending", id="pipe-4")
        yield Static(" ─────●───── ", id="connector-4")
        yield PipelineStage("Reporting", 0, 2, "pending", id="pipe-5")

    def update_stages(self, stages: list[dict]) -> None:
        for i, stage in enumerate(stages):
            wid = self.query_one(f"#pipe-{i}", PipelineStage)
            wid._stage_completed = stage["completed"]
            wid._stage_total = stage["total"]
            wid._stage_status = stage["status"]
            wid.refresh()

class AgentLogPanel(Vertical):
    """Agent log with scrollable output"""
    def compose(self) -> ComposeResult:
        with Horizontal(id="log-title-bar"):
            yield Static("PORT SCANNING AGENT", id="log-agent-name")
            yield Static("● RUNNING", id="log-agent-status")
            yield Static("00:02:47", id="log-agent-timer")
        yield RichLog(id="agent-log-output", highlight=True, markup=True, max_lines=100)

    def append_log(self, line: str) -> None:
        log = self.query_one("#agent-log-output", RichLog)
        t = Text()
        if line.startswith("> "):
            t.append(line, style=Style(color="#00ff41", bold=True))
        elif line.startswith("  "):
            t.append(line, style=Style(color="#4a7a4a"))
        else:
            t.append(line, style=Style(color="#c8ffc8"))
        log.write(t)

class ThinkingBox(Vertical):
    """Collapsible thinking/reasoning box"""
    def compose(self) -> ComposeResult:
        with Horizontal(id="thinking-header"):
            yield Static("THINKING — PORT SCANNING AGENT", id="thinking-title")
            yield Pulse(id="thinking-pulse")
        with Vertical(id="thinking-content"):
            yield Static("> Goal: Identify all open ports and running services", classes="think-line")
            yield Static("> Reasoning: Comprehensive port scan with service detection", classes="think-line")
            yield Static("> Approach: naabu + nmap for speed and accuracy", classes="think-line")
            yield Static("> Focus: High-priority services, versions, and potential vulnerabilities", classes="think-line")
            yield Static("> Next: Analyze services and identify enumeration opportunities", classes="think-line")
        yield Static("TOKENS: 12.4k", id="tokens-footer")

class ActivityFeed(Vertical):
    """Bottom section: Activity feed with table"""
    def compose(self) -> ComposeResult:
        with Horizontal(id="activity-header"):
            yield Static("ACTIVITY FEED", id="activity-title")
            yield Static("VERBOSITY [High ▼]", id="verbosity-selector")
        yield DataTable(id="activity-table")

    def on_mount(self) -> None:
        table = self.query_one("#activity-table", DataTable)
        table.add_columns("Time", "Agent", "Event")
        table.add_rows([
            ("06:11:02", "Subdomain Enum", "Discovered 23 subdomains"),
            ("06:11:15", "Port Scanner", "Found 4 open ports"),
            ("06:11:22", "Content Discov", "Started web crawling on 4 targets"),
            ("06:11:35", "Tech Analysis", "Detecting technologies and frameworks"),
            ("06:11:42", "Orchestrator", "Updated attack graph with 8 new nodes"),
        ])

    def update_feed(self, rows: list[tuple]) -> None:
        table = self.query_one("#activity-table", DataTable)
        table.clear()
        table.add_rows(rows)


class CenterPanel(Vertical):
    """Center panel — Pipeline, Log, Thinking, Activity (50%)"""
    def compose(self) -> ComposeResult:
        yield PipelineStepper(id="pipeline-stepper")
        yield AgentLogPanel(id="agent-log-panel")
        yield ThinkingBox(id="thinking-box")
        yield ActivityFeed(id="activity-feed")


# ============================================================
# RIGHT PANEL
# ============================================================
class TargetOverview(Vertical):
    """Section 1: Target overview card"""
    def compose(self) -> ComposeResult:
        yield Static("TARGET OVERVIEW", id="target-overview-title")
        yield Static("Primary Target:    evil.com", classes="target-info")
        yield Static("IP Address:        93.184.216.34", classes="target-info")
        yield Static("Open Ports:        4", classes="target-info")
        yield Static("Subdomains:        3", classes="target-info")
        yield Static("Technologies:      7", classes="target-info")
        with Horizontal(id="attack-surface"):
            yield Static("Attack Surface:    ", classes="target-info")
            yield Static("Medium", id="risk-badge")

    def update_info(self, info: dict) -> None:
        self.query_one("#risk-badge", Static).update(info.get("risk", "Unknown"))

class AttackGraph(Vertical):
    """Section 2: ASCII attack graph visualization"""
    ATTACK_GRAPH = """
         [🌐 evil.com]
        /       |        \\
[api.evil] [client.e] [assets.e]
     |              |
[Auth API]    [Web App PHP]   [CDN CF]
     |              |
 [Login]      [Admin]     [Upload]
                   |
           [MySQL] [Redis] [MongoDB]
"""
    def compose(self) -> ComposeResult:
        yield Static("ATTACK GRAPH", id="attack-graph-title")
        yield Static(self.ATTACK_GRAPH, id="attack-graph-content")
        yield Static("● Host  ● Service  ◆ Application  ● Data Store  ○ External", id="graph-legend")

class KeyFindings(Vertical):
    """Section 3: Key findings and risk score"""
    def compose(self) -> ComposeResult:
        yield Static("KEY FINDINGS", id="findings-title")
        yield Static("✓ 4 open ports discovered", classes="finding-item")
        yield Static("✓ 3 subdomains enumerated", classes="finding-item")
        yield Static("✓ Web application detected", classes="finding-item")
        yield Static("✓ Multiple technologies identified", classes="finding-item")
        yield Static("✓ Potential attack vectors mapped", classes="finding-item")
        with Vertical(id="risk-score-panel"):
            yield Static("RISK SCORE", id="risk-score-title")
            yield Static("   4.2", id="risk-score-value")
            yield Static("  Medium", id="risk-score-label")
            yield Static("[████████░░]", id="risk-score-bar")

class TechList(Vertical):
    """Section 4: Top technologies with bars"""
    def compose(self) -> ComposeResult:
        yield Static("TOP TECHNOLOGIES", id="tech-title")
        yield Static("PHP 8.1.2    45% [████████░░]", classes="tech-item")
        yield Static("Nginx        30% [██████░░░░]", classes="tech-item")
        yield Static("Cloudflare   15% [███░░░░░░░]", classes="tech-item")
        yield Static("jQuery       10% [██░░░░░░░░]", classes="tech-item")

class RecentDiscoveries(Vertical):
    """Section 5: Recent discoveries list"""
    def compose(self) -> ComposeResult:
        yield Static("RECENT DISCOVERIES", id="recent-title")
        yield Static("api.evil.com      06:11:02", classes="discovery-item")
        yield Static("client.evil.com   06:11:03", classes="discovery-item")
        yield Static("assets.evil.com   06:11:04", classes="discovery-item")
        yield Static("MySQL 8.0.32      06:11:38", classes="discovery-item")
        yield Static("Redis 6.2.11      06:11:39", classes="discovery-item")

class SessionMetrics(Vertical):
    """Section 6: Session metrics panel"""
    def compose(self) -> ComposeResult:
        yield Static("SESSION METRICS", id="metrics-title")
        yield Static("Commands Executed   47", classes="metric-item")
        yield Static("Data Collected      12.4 MB", classes="metric-item")
        yield Static("Findings            19", classes="metric-item")
        yield Static("Vulnerabilities     0", classes="metric-item")
        yield Static("Time Elapsed        00:02:47", classes="metric-item")

    def update_metrics(self, stats: dict) -> None:
        uptime = stats.get("uptime", 0)
        uptime_str = str(timedelta(seconds=int(uptime)))
        self.query_one("#metrics-title", Static)
        # Find and update each metric
        for child in self.children:
            if isinstance(child, Static) and child is not self.children[0]:
                text = str(child.renderable) if hasattr(child, 'renderable') else ""
                if text.startswith("Commands Executed"):
                    child.update(f"Commands Executed   {stats.get('commands', 0)}")
                elif text.startswith("Data Collected"):
                    child.update(f"Data Collected      {stats.get('data_collected', 0):.1f} MB")
                elif text.startswith("Findings"):
                    child.update(f"Findings            {stats.get('findings', 0)}")
                elif text.startswith("Vulnerabilities"):
                    child.update(f"Vulnerabilities     {stats.get('vulnerabilities', 0)}")
                elif text.startswith("Time Elapsed"):
                    child.update(f"Time Elapsed        {uptime_str}")


class RightPanel(VerticalScroll):
    """Right panel — Target info, Attack Graph, Findings, Tech, Discoveries, Metrics (30%)"""
    def compose(self) -> ComposeResult:
        yield TargetOverview(id="target-overview")
        yield AttackGraph(id="attack-graph")
        yield KeyFindings(id="key-findings")
        yield TechList(id="tech-list")
        yield RecentDiscoveries(id="recent-discoveries")
        yield SessionMetrics(id="session-metrics")


# ============================================================
# MODAL SCREENS
# ============================================================
class HelpScreen(ModalScreen[None]):
    """Help modal screen"""
    CSS = """
    HelpScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.85);
    }
    #help-dialog {
        width: 60;
        height: 70%;
        background: #050f05;
        border: solid #1a3a1a;
        padding: 1 2;
    }
    #help-title {
        text-align: center;
        color: #00ff41;
        text-style: bold;
        margin-bottom: 1;
    }
    #help-content {
        height: 1fr;
        margin-bottom: 1;
    }
    .help-line {
        color: #c8ffc8;
        margin-bottom: 1;
    }
    .help-key {
        color: #ffb300;
        text-style: bold;
    }
    """
    BINDINGS = [Binding("escape", "dismiss", "Close", priority=True)]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Static("HELP — ARGUS v0.8.3", id="help-title")
            with VerticalScroll(id="help-content"):
                yield Static("Keyboard Shortcuts:", classes="help-line")
                yield Static("  [?] or F1    Show this help", classes="help-line")
                yield Static("  Ctrl+K       Command palette", classes="help-line")
                yield Static("  Tab          Auto-complete", classes="help-line")
                yield Static("  Ctrl+D       Exit", classes="help-line")
                yield Static("", classes="help-line")
                yield Static("Commands:", classes="help-line")
                yield Static("  scan <target>    Start a new scan", classes="help-line")
                yield Static("  status           Show system status", classes="help-line")
                yield Static("  agents           List agents", classes="help-line")
                yield Static("  findings         Show findings", classes="help-line")
                yield Static("  help             This message", classes="help-line")
            yield Static("Press ESC to close", id="help-close")

    def action_dismiss(self) -> None:
        self.dismiss(None)


# ============================================================
# MAIN APP
# ============================================================
class ArgusApp(App):
    """ARGUS v0.8.3 — Autonomous AI Cybersecurity Cockpit TUI"""
    CSS_PATH = "argus.tcss"

    BINDINGS = [
        Binding("ctrl+k", "show_commands", "Commands"),
        Binding("ctrl+d", "quit", "Quit"),
        Binding("tab", "autocomplete", "Complete"),
        Binding("?", "show_help", "Help", priority=True),
        Binding("f1", "show_help", "Help", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True),
    ]

    def __init__(self):
        super().__init__()
        # ============================================================
        # INTEGRATION HOOK: Replace with your actual ARGUS backend
        # ============================================================
        self.backend = ArgusBackend()
        self.demo = DemoDataGenerator(self.backend)
        self._demo_mode = True  # Set False when using real backend
        self._agent_output_streams: dict[str, asyncio.Task] = {}
        self._current_agent = "Port Scanner"
        self._log_timer = 0

    def compose(self) -> ComposeResult:
        yield ArgusHeader(id="argus-header")
        with Horizontal(id="main-content"):
            yield LeftPanel(id="left-panel")
            yield CenterPanel(id="center-panel")
            yield RightPanel(id="right-panel")
        yield ArgusFooter(id="argus-footer")

    def on_mount(self) -> None:
        """Initialize and start all update loops"""
        if self._demo_mode:
            self.set_interval(1, self._demo_update)
            self.set_interval(2, self._demo_stream_log)

    def _demo_update(self) -> None:
        """Pull data from backend and update all reactive panels"""
        stats = self.backend.get_system_stats()
        try:
            self.query_one(SysHealthBars).update(stats)
        except Exception:
            pass
        try:
            self.query_one(SessionMetrics).update_metrics(stats)
        except Exception:
            pass
        try:
            stages = self.backend.get_pipeline_stages()
            self.query_one(PipelineStepper).update_stages(stages)
        except Exception:
            pass

    def _demo_stream_log(self) -> None:
        """Simulate streaming agent output to log panel"""
        line = self.demo.get_next_log_line(self._current_agent)
        if line:
            try:
                self.query_one(AgentLogPanel).append_log(line)
            except Exception:
                pass

    # ============================================================
    # INTEGRATION HOOK: Replace with real agent output streaming
    # ============================================================
    async def stream_agent_output(self, agent_name: str) -> None:
        """Stream output from a running agent to the log panel.
        Replace the body with your actual async generator:
        
        async for line in self.backend.stream_output(agent_name):
            self.query_one(AgentLogPanel).append_log(line)
        """
        # Demo mode: already handled by _demo_stream_log
        pass

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_show_commands(self) -> None:
        self.query_one("#command-input", Input).focus()

    def action_autocomplete(self) -> None:
        inp = self.query_one("#command-input", Input)
        candidates = ["scan ", "status", "agents", "findings", "help"]
        for c in candidates:
            if c.startswith(inp.value.strip()):
                inp.value = c + " "
                inp.action_cursor_to_end()
                break

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "command-input":
            cmd = event.input.value.strip()
            if cmd:
                # ============================================================
                # INTEGRATION HOOK: Send to real backend
                # result = self.backend.run_command(cmd)
                # ============================================================
                result = self.backend.run_command(cmd)
                try:
                    self.query_one(AgentLogPanel).append_log(f"> {cmd}")
                    self.query_one(AgentLogPanel).append_log(f"  {result}")
                except Exception:
                    pass
                event.input.value = ""


def main():
    """Entry point for running the TUI standalone"""
    app = ArgusApp()
    app.run()


if __name__ == "__main__":
    main()
