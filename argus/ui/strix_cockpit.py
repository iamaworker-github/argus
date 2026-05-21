"""
STRIX tactical cockpit for ARGUS.

This module implements a terminal-native operational cockpit using Textual,
Rich, and asyncio. It is intentionally dense and monochrome-first: thin
borders, compact telemetry, structured streams, and keyboard driven control.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

from textual.app import App
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widgets import Button, Input, RichLog, Static

from argus.core.chain_matrix import find_matching_chains, CHAINS
from argus.core.graph_memory import get_graph_memory
from argus.core.logger import get_logger
from argus.core.attack_surface import get_attack_surface, SurfaceCategory
from argus.core.learning_engine import get_learning_engine
from argus.core.no_exploit_no_report import ProductionSafeValidator
from argus.agents.base_agent import Finding

logger = get_logger()

C = {
    "bg": "#05070b",
    "panel": "#090d14",
    "surf": "#0d1420",
    "line": "#1f2a38",
    "line2": "#27384a",
    "text": "#d1d5db",
    "dim": "#7b8494",
    "muted": "#4b5563",
    "cyan": "#58a6ff",
    "blue": "#38bdf8",
    "purple": "#a78bfa",
    "green": "#39d353",
    "amber": "#facc15",
    "orange": "#fb923c",
    "red": "#ef4444",
}

THEMES = {
    "pentest": {"p": C["green"], "l": "PENTEST", "model": "gpt-5.4/security"},
    "osint": {"p": C["red"], "l": "OSINT", "model": "gpt-5.4/osint"},
    "ctf": {"p": C["cyan"], "l": "CTF", "model": "gpt-5.4/ctf"},
    "bb": {"p": C["purple"], "l": "BBAUNTY", "model": "gpt-5.4/bugbounty"},
}


@dataclass
class AgentState:
    name: str
    status: str
    progress: int = 0
    children: List[str] = field(default_factory=list)
    synced: bool = False


@dataclass
class GraphNode:
    label: str
    kind: str = "host"
    detail: str = ""
    parent: str = ""
    active: bool = False


@dataclass
class Finding:
    title: str
    severity: str
    confidence: float = 0.5
    chain: str = ""


class QuitModal(ModalScreen):
    """Confirmation screen for closing the cockpit."""

    def compose(self):
        yield Container(
            Static("Quit STRIX?", classes="qt"),
            Static("Session telemetry and findings remain persisted.", classes="qs"),
            Horizontal(
                Button("Yes", variant="primary", id="y"),
                Button("No", variant="default", id="n"),
                classes="qb",
            ),
            classes="qx",
        )

    def on_button_pressed(self, e):
        if e.button.id == "y":
            self.app.exit()
        else:
            self.dismiss()


class PanelTitle(Static):
    """Small helper to keep panel titles consistent."""

    def render(self):
        return self.visual or " "

    def set_status(self, title: str, status: str = "", color: str = C["cyan"]) -> None:
        suffix = f"  [dim]•[/] [{color}]{status}[/]" if status else ""
        self.update(f"[{C['cyan']}]{title}[/]{suffix}")


class AgentTree(Static):
    """Compact orchestration tree with stable public state for tests."""

    def __init__(self, **kwargs):
        super().__init__(" ", **kwargs)
        self._a: Dict[str, Tuple[str, int, List[str], bool]] = {}

    def render(self):
        return self.visual or " "

    def set(self, name, status, pct=0, kids=None, sync=False):
        self._a[name] = (status, pct, kids or [], sync)
        self._refresh_view()

    def _refresh_view(self) -> None:
        rows = []
        colors = {
            "running": C["green"],
            "completed": C["green"],
            "failed": C["red"],
            "queued": C["amber"],
            "waiting": C["purple"],
            "idle": C["dim"],
        }
        icons = {
            "running": "▣",
            "completed": "✓",
            "failed": "✗",
            "queued": "◌",
            "waiting": "◇",
            "idle": "○",
        }
        agent_icons = {
            "Subdomain Enum": ("☁", C["green"]),
            "Port Scanner": ("◉", C["cyan"]),
            "Content Discovery": ("◇", C["purple"]),
            "Tech Analysis": ("◈", C["amber"]),
        }
        for name, (status, pct, children, synced) in self._a.items():
            color = colors.get(status, C["dim"])
            icon, icon_color = agent_icons.get(name, (icons.get(status, "○"), color))
            status_text = "Queued" if status == "queued" else "Running" if status in {"running", "waiting"} else status.title()
            line = f" [{icon_color}]{icon}[/] [bold]{name[:18]:18s}[/] [{color}]{status_text:>8s}[/]"
            if name == "Port Scanner":
                line = f"[white on #082033]{line}[/]"
            rows.append(line)
        self.update("\n".join(rows) if rows else f"[{C['dim']}]idle[/]")


class FindSum(Static):
    """Findings summary with severity distribution and risk meter."""

    def __init__(self, **kwargs):
        super().__init__(" ", **kwargs)
        self._f: List[Tuple[str, str, float, str]] = []

    def render(self):
        return self.visual or " "

    def add(self, title, sev, conf=0.5, chain=""):
        self._f.append((title, sev, conf, chain))
        self._refresh_view()

    def _refresh_view(self) -> None:
        if not self._f:
            self.update(f"[{C['dim']}]no findings yet[/]")
            return

        severity_weight = {"critical": 10, "high": 7, "medium": 4, "low": 2, "info": 1}
        sev_colors = {
            "critical": C["red"],
            "high": C["orange"],
            "medium": C["amber"],
            "low": C["cyan"],
            "info": C["dim"],
        }
        score = min(9.9, sum(severity_weight.get(sev, 1) * conf for _, sev, conf, _ in self._f) / 3.3)
        meter_fill = max(1, min(10, int(score)))
        meter = (
            f"[{C['green']}]{'■' * min(meter_fill, 3)}[/]"
            f"[{C['amber']}]{'■' * max(0, min(meter_fill - 3, 4))}[/]"
            f"[{C['red']}]{'■' * max(0, meter_fill - 7)}[/]"
            f"[{C['muted']}]{'■' * (10 - meter_fill)}[/]"
        )
        rows = [
            f"[{C['dim']}]RISK SCORE[/] [{C['amber']}]{score:0.1f}[/]  {meter}",
            f"[{C['dim']}]FINDINGS[/]   {len(self._f):<2d}    [{C['dim']}]CONF[/] {self._avg_conf():.0%}",
            "",
        ]
        sorted_findings = sorted(
            self._f,
            key=lambda item: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(item[1], 9),
        )
        for title, sev, conf, chain in sorted_findings[:8]:
            color = sev_colors.get(sev, C["dim"])
            rows.append(f"[{color}]■ {sev.upper():8s}[/] {title[:34]:34s} [{C['dim']}]{conf:.0%}[/]")
            if chain:
                rows.append(f"  [{C['dim']}]chain: {chain[:39]}[/]")
        self.update("\n".join(rows))

    def _avg_conf(self) -> float:
        return sum(conf for _, _, conf, _ in self._f) / max(1, len(self._f))


class ThinkStream(Static):
    """Structured AI cognition stream; no prose walls."""

    def __init__(self, **kwargs):
        super().__init__(" ", **kwargs)
        self._b: Deque[Tuple[str, str]] = deque(maxlen=48)

    def render(self):
        return self.visual or " "

    def add(self, section, msg):
        normalized = section if str(section).startswith("[") else f"[{str(section).strip(':').upper()}]"
        self._b.append((normalized, msg))
        self._refresh_view()

    def _refresh_view(self) -> None:
        rows = []
        section_colors = {
            "[OBJECTIVE]": C["cyan"],
            "[TACTICAL PLAN]": C["green"],
            "[HYPOTHESIS]": C["purple"],
            "[NEXT ACTION]": C["cyan"],
            "[RISK]": C["amber"],
            "[DISCOVERED RELATIONSHIPS]": C["green"],
        }
        for section, msg in list(self._b)[-12:]:
            color = section_colors.get(section, C["purple"])
            rows.append(f"[{color}]{section:<26s}[/] {msg}")
        self.update("\n".join(rows))


class GraphViz(Static):
    """Layered attack graph renderer using terminal-safe Unicode lines."""

    def __init__(self, **kwargs):
        super().__init__(" ", **kwargs)
        self._n: List[Tuple[str, str]] = []
        self.nodes: Dict[str, GraphNode] = {}
        self._pulse = False

    def render(self):
        return self.visual or " "

    def add(self, label, parent="", kind: str = "host", detail: str = "", active: bool = False):
        self._n.append((label, parent))
        if label not in self.nodes:
            self.nodes[label] = GraphNode(label=label, parent=parent, kind=kind, detail=detail, active=active)
        else:
            node = self.nodes[label]
            node.parent = parent or node.parent
            node.kind = kind or node.kind
            node.detail = detail or node.detail
            node.active = active or node.active
        self._refresh_view()

    def pulse(self) -> None:
        self._pulse = not self._pulse
        self._refresh_view()

    def _children(self, parent: str) -> List[GraphNode]:
        return [node for node in self.nodes.values() if node.parent == parent]

    def _format_node(self, node: GraphNode, width: int = 18) -> str:
        palette = {
            "host": C["green"],
            "service": C["cyan"],
            "app": C["purple"],
            "data": C["amber"],
            "cloud": C["red"],
            "external": C["dim"],
        }
        icon = {
            "host": "◎",
            "service": "▣",
            "app": "◈",
            "data": "◇",
            "cloud": "◉",
            "external": "○",
        }.get(node.kind, "○")
        color = palette.get(node.kind, C["dim"])
        marker = "◆" if node.active and self._pulse else icon
        label = f"{marker} {node.label[: width - 4]:<{width - 4}s}"
        detail = f" {node.detail[: width - 2]:<{width - 2}s}" if node.detail else ""
        return f"[{color}]{label}[/]" + (f"\n[{C['dim']}]{detail}[/]" if detail else "")

    def _refresh_view(self) -> None:
        if not self.nodes:
            self.update(f"[{C['dim']}]awaiting graph telemetry[/]")
            return
        root = next((node for node in self.nodes.values() if not node.parent), next(iter(self.nodes.values())))
        l1 = self._children(root.label)[:3]
        l2: List[GraphNode] = []
        for node in l1:
            l2.extend(self._children(node.label)[:2])
        l3: List[GraphNode] = []
        for node in l2:
            l3.extend(self._children(node.label)[:3])

        root_line = self._format_node(root, 24).splitlines()[0]
        rows = [f"                         {root_line}", f"              [{C['line2']}]┌────────────┼────────────┐[/]"]
        rows.extend(self._row(l1, 3, 22))
        if l2:
            rows.append(f"              [{C['line2']}]│            │            │[/]")
            rows.extend(self._row(l2[:3], 3, 22))
        if l3:
            rows.append(f"              [{C['line2']}]│            │            │[/]")
            rows.extend(self._row(l3[:3], 3, 22))
        rows.extend(
            [
                "",
                f"[{C['green']}]●[/] Host  [{C['cyan']}]●[/] Service  [{C['purple']}]●[/] App  "
                f"[{C['amber']}]●[/] Data  [{C['red']}]●[/] Cloud  [{C['dim']}]●[/] External",
            ]
        )
        self.update("\n".join(rows))

    def _row(self, nodes: Iterable[GraphNode], columns: int, width: int) -> List[str]:
        entries = [self._format_node(node, width).splitlines() for node in nodes]
        while len(entries) < columns:
            entries.append([f"{'':{width}s}", f"{'':{width}s}"])
        first = "  ".join(item[0] for item in entries[:columns])
        second = "  ".join((item[1] if len(item) > 1 else f"{'':{width}s}") for item in entries[:columns])
        return [first, second]


class PipelineView(Static):
    def __init__(self, **kwargs):
        super().__init__(" ", **kwargs)
        self._phase = 1

    def render(self):
        return self.visual or " "

    def set_phase(self, phase: int):
        self._phase = max(0, min(5, phase))
        phases = [
            ("Reconnaissance", "4/4", C["green"]),
            ("Enumeration", "3/4", C["cyan"]),
            ("Analysis", "1/3", C["purple"]),
            ("Vulnerability", "0/4", C["amber"]),
            ("Exploitation", "0/2", C["red"]),
            ("Reporting", "0/2", C["dim"]),
        ]
        labels = []
        scores = []
        for index, (label, score, color) in enumerate(phases):
            if index == self._phase:
                labels.append(f"[{color} on #082033] {label:^15s} [/]")
            else:
                labels.append(f"[{color}]• {label[:14]:14s}[/]")
            scores.append(f"[{color}]{score:^15s}[/]")
        self.update("──".join(labels) + "\n" + "  ".join(scores))


class ActivityFeed(RichLog):
    def __init__(self, **kwargs):
        super().__init__(highlight=True, markup=True, max_lines=120, **kwargs)

    def log(self, cat, msg):
        colors = {
            "asset": C["cyan"],
            "agent": C["green"],
            "disc": C["purple"],
            "vuln": C["amber"],
            "fail": C["red"],
            "orch": C["blue"],
        }
        color = colors.get(cat, C["dim"])
        self.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/]  [{color}]{cat[:5].upper():5s}[/]  {msg}")


class StrixCockpit(App):
    """Terminal-native STRIX operational cockpit."""

    CSS_PATH = "strix_cockpit.tcss"
    TITLE = "ARGUS"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "cmd", "Cmd"),
        Binding("f2", "mode", "Mode"),
        Binding("f11", "full", "Full"),
    ]

    def __init__(self, target=None):
        super().__init__()
        self.target = target or "evil.com"
        self._g = get_graph_memory()
        self._t0 = time.time()
        self._mi = 0
        self._mk = ["pentest", "osint", "ctf", "bb"]
        self._theme = THEMES["pentest"]
        self._session = f"{abs(hash(self._t0)) % 0xFFFFFF:06x}"
        self._tokens_in = 1_230_000
        self._tokens_out = 420_000
        self._commands = 0
        self._data_mb = 0.0
        self._simulation_task: Optional[asyncio.Task] = None
        self._findings_count = 0
        self._discovered_endpoints: List[str] = []
        self._discovered_technologies: List[str] = []
        self._ai_plan_categories: List[str] = []
        self._ai_plan_reason = ""
        self._scan_complete = False
        self._surface = get_attack_surface(target or "unknown")
        self._learning = get_learning_engine()
        self._validator = ProductionSafeValidator()
        self._attack_paths: List[dict] = []
        self._validation_stats = {"validated": 0, "rejected": 0, "pending": 0, "production_safe": 0}
        self._surface_stats: dict = {}

    def compose(self):
        with Horizontal(id="topbar"):
            yield Static("ARGUS", id="brand")
            yield Static("v0.0.3", id="version-pill")
            yield Static("See Everything Miss Noting !!!", id="subtitle")
            yield Static(id="operation")
            yield Static(id="target-pill")
            yield Static(id="session-pill")
            yield Static(id="model-pill")
            yield Static(id="clock")
            yield Static(id="token-pill")
            yield Static("● LIVE", id="live")

        with Horizontal(id="main"):
            with Vertical(id="left"):
                with Vertical(classes="panel status-panel"):
                    yield PanelTitle("STATUS", classes="panel-title")
                    yield Static(id="status-head-content")
                with Vertical(classes="panel agents-panel"):
                    yield PanelTitle("AGENTS [4/4]", classes="panel-title")
                    yield Static(id="agent-list")
                with Vertical(classes="panel system-panel"):
                    yield PanelTitle("SYSTEM HEALTH", classes="panel-title")
                    yield Static(id="syshealth")

            with Vertical(id="center"):
                with Vertical(classes="panel pipeline-panel"):
                    yield PanelTitle("OPERATION PIPELINE", classes="panel-title")
                    yield PipelineView(id="pipeline")
                with Horizontal(id="work-grid"):
                    with Vertical(id="work-left"):
                        with Vertical(classes="panel exec-panel"):
                            yield PanelTitle("LIVE EXECUTION STREAM", id="exec-title", classes="panel-title")
                            yield RichLog(id="exec", highlight=True, markup=True, max_lines=300)
                        with Vertical(classes="panel thinking-panel"):
                            yield PanelTitle("AI COGNITION STREAM", id="think-title", classes="panel-title")
                            yield ThinkStream(id="think")
                        with Vertical(classes="panel activity-panel"):
                            yield PanelTitle("ACTIVITY FEED", classes="panel-title")
                            yield ActivityFeed(id="feed")
                    with Vertical(id="work-right"):
                        with Vertical(classes="panel graph-panel"):
                            yield PanelTitle("ATTACK GRAPH", classes="panel-title")
                            yield GraphViz(id="graph")
                        with Vertical(classes="panel findings-panel"):
                            yield PanelTitle("FINDINGS SUMMARY", classes="panel-title")
                            yield FindSum(id="find")

            with Vertical(id="right"):
                with Vertical(classes="panel target-panel"):
                    yield PanelTitle("TARGET INTELLIGENCE", classes="panel-title")
                    yield Static(id="intel")
                with Vertical(classes="panel tech-panel"):
                    yield PanelTitle("ATTACK SURFACE", classes="panel-title")
                    yield Static(id="surface")
                with Vertical(classes="panel attack-paths-panel"):
                    yield PanelTitle("ATTACK PATHS", classes="panel-title")
                    yield Static(id="attack-paths")
                with Vertical(classes="panel validation-panel"):
                    yield PanelTitle("VALIDATION STATUS", classes="panel-title")
                    yield Static(id="validation")
                with Vertical(classes="panel intelligence-panel"):
                    yield PanelTitle("INTELLIGENCE", classes="panel-title")
                    yield Static(id="intelligence")
                with Vertical(classes="panel metrics-panel"):
                    yield PanelTitle("SESSION METRICS", classes="panel-title")
                    yield Static(id="smetrics")

        with Horizontal(id="commandbar"):
            yield Static("argus@cockpit:~#", id="prompt")
            yield Input(id="cmd", placeholder="command or AI assist...")
            yield Static("? help   /scan target   /graph q   /chain q   /surface   /learn   F2 mode   F11 focus   q quit", id="command-help")

    def on_mount(self):
        self._paint_bar()
        self._paint_mission()
        self._paint_intel()
        self.query_one("#pipeline", PipelineView).set_phase(1)
        self._boot_real()
        self.set_interval(0.7, self._blink_live)
        self.set_interval(1, self._paint_bar)
        self.set_interval(1.5, self._paint_mission)
        self.set_interval(1.1, lambda: self.query_one("#graph", GraphViz).pulse())
        self.set_interval(2.0, self._paint_intel)
        self._simulation_task = asyncio.create_task(self._run_real_scan())

    def _paint_bar(self):
        elapsed = time.time() - self._t0
        try:
            self.query_one("#operation", Static).update(
                f"[{C['green']}]OPERATION:[/] [{C['text']}]{self._theme['l']}[/]"
            )
            self.query_one("#target-pill", Static).update(f"[{C['green']}]TARGET:[/] [{C['text']}]{self.target}[/]")
            self.query_one("#session-pill", Static).update(f"[{C['green']}]SESSION:[/] [{C['text']}]{self._session}[/]")
            self.query_one("#model-pill", Static).update(f"[{C['green']}]MODEL:[/] [{C['text']}]{self._theme['model']}[/]")
            self.query_one("#clock", Static).update(
                f"[{C['green']}]TIME:[/] [{C['text']}]{int(elapsed // 60):02d}:{int(elapsed % 60):02d}[/]"
            )
            self.query_one("#token-pill", Static).update(
                f"[{C['green']}]TOKENS:[/] [{C['text']}]{(self._tokens_in + self._tokens_out) / 1_000_000:.1f}M[/]"
            )
        except NoMatches:
            pass

    def _paint_mission(self):
        entities = len(self._g._entities)
        elapsed = time.time() - self._t0
        cpu = 21 + int(elapsed) % 12
        mem = 39 + int(elapsed / 2) % 10
        net = 9 + int(elapsed / 3) % 18
        try:
            from argus.core.adaptive_concurrency import get_adaptive_concurrency
            acc = get_adaptive_concurrency()

            # Status section: bird logo + status + safe mode
            status_head = (
                f"  [bold {C['green']}]🦅  ARGUS[/]\n"
                f"  [{C['green']}]●[/] [bold]EXECUTING[/]\n"
                f"  [{C['dim']}]MODE[/]           [{C['text']}]Autonomous[/]\n"
                f"  [{C['dim']}]RISK PROFILE[/]   [{C['text']}]Balanced[/]\n"
                f"  [{C['dim']}]MAX PARALLEL[/]   [{C['text']}]4 agents[/]\n"
                f"  [{C['dim']}]SAFE MODE[/]      [{C['green']}]ON[/]"
            )
            self.query_one("#status-head-content", Static).update(status_head)

            # Agent list: subdomain enum, port scanner, content discovery, tech analysis
            agent_names = [
                ("Subdomain Enum", "running", C["green"]),
                ("Port Scanner", "running", C["cyan"]),
                ("Content Discovery", "running", C["purple"]),
                ("Tech Analysiss", "queued", C["amber"]),
            ]
            agent_lines = []
            colors = {"completed": C["green"], "running": C["green"], "queued": C["amber"], "failed": C["red"]}
            icons = {"completed": "●", "running": "●", "queued": "●", "failed": "●"}
            for name, status, _ in agent_names:
                c = colors.get(status, C["dim"])
                icon = icons.get(status, "○")
                status_text = status.title()
                agent_lines.append(f"  [{c}]{icon}[/] {name:<18s} [{c}]{status_text:>8s}[/]")
            agent_lines.extend([
                "",
                f"  [{C['cyan']}]＋[/] [bold]New Agent[/]     [{C['cyan']}]Launch[/]",
                f"  [{C['green']}]◉[/] Orchestrator    [{C['green']}]Active[/]",
                f"  [{C['amber']}]◉[/] Memory          [{C['amber']}]87%[/]",
                f"  [{C['green']}]◉[/] Knowledge Base  [{C['green']}]Synced[/]",
            ])
            self.query_one("#agent-list", Static).update("\n".join(agent_lines))

            # System health: CPU, MEM, NET, Tokens, Credits, Uptime
            health = (
                self._metric("CPU", cpu, C["green"])
                + "\n"
                + self._metric("MEM", mem, C["green"])
                + "\n"
                + self._metric("NET", net, C["green"])
                + "\n\n"
                f"  [{C['dim']}]TOKENS[/]   [{C['text']}]{(self._tokens_in + entities * 1300) / 1_000_000:.1f}M / 2.0M[/]\n"
                f"  [{C['dim']}]MEMORY[/]   [{C['green']}]{87 + entities % 8}% synced[/]\n"
                f"  [{C['dim']}]CREDITS[/]  [{C['text']}]{4872 - entities * 3:,}[/]\n"
                f"  [{C['dim']}]UPTIME[/]   [{C['text']}]{int(elapsed // 60):02d}:{int(elapsed % 60):02d}[/]"
            )
            self.query_one("#syshealth", Static).update(health)
        except NoMatches:
            pass

    def _paint_intel(self):
        entities = len(self._g._entities)
        elapsed = int(time.time() - self._t0)
        try:
            tech_str = "\n".join([f"[{C['cyan']}]◎[/] {t:<16s}" for t in self._discovered_technologies[:6]]) if self._discovered_technologies else f"[{C['dim']}]Scanning...[/]"
            ep_str = "\n".join([f"{e[:28]:28s}" for e in self._discovered_endpoints[:6]]) if self._discovered_endpoints else f"[{C['dim']}]Scanning...[/]"
            ai_str = f"[{C['purple']}]AI Plan:[/] {', '.join(self._ai_plan_categories)}" if self._ai_plan_categories else f"[{C['dim']}]Planning...[/]"

            self.query_one("#intel", Static).update(
                f"[{C['dim']}]Primary Target[/]\n"
                f"[bold]{self.target}[/]\n\n"
                f"{ai_str}\n"
                f"[{C['dim']}]Endpoints[/]       {len(self._discovered_endpoints)}\n"
                f"[{C['dim']}]Technologies[/]    {len(self._discovered_technologies)}\n"
                f"[{C['dim']}]Status[/]          [{'green' if self._scan_complete else 'amber'}]{'COMPLETE' if self._scan_complete else 'SCANNING'}[/]"
            )

            # Attack Surface Panel
            surface_summary = self._surface.get_summary()
            self._surface_stats = surface_summary
            pending = surface_summary.get("pending", 0)
            explored = surface_summary.get("explored", 0)
            coverage = surface_summary.get("coverage_pct", 0)
            next_path = self._surface.get_next_attack_path()
            next_str = f"  Next: [{C['cyan']}]{next_path.value[:30]}[/]" if next_path else f"  [{C['dim']}]All explored[/]"
            self.query_one("#surface", Static).update(
                f"[{C['dim']}]Total Surface[/]    {surface_summary.get('total_surface', 0)}\n"
                f"[{C['dim']}]Explored[/]         {explored}\n"
                f"[{C['dim']}]Pending[/]          [{C['amber']}]{pending}[/]\n"
                f"[{C['dim']}]Coverage[/]         [{C['green']}]{coverage}%[/]\n"
                f"{next_str}\n"
                f"[{C['dim']}]Categories[/]       {len(surface_summary.get('categories', {}))}"
            )

            # Attack Paths Panel
            if self._attack_paths:
                ap_lines = []
                for ap in self._attack_paths[:4]:
                    color = C["red"] if ap.get("severity") == "critical" else C["amber"] if ap.get("severity") == "high" else C["cyan"]
                    confidence = ap.get("confidence", 0)
                    ap_lines.append(
                        f"[{color}]▸[/] {ap.get('chain_name', '')[:22]:22s} "
                        f"[{C['dim']}]{ap.get('steps_completed', 0)}/{ap.get('total_steps', 0)}[/] "
                        f"[{color}]{confidence:.0%}[/]"
                    )
                self.query_one("#attack-paths", Static).update("\n".join(ap_lines))
            else:
                self.query_one("#attack-paths", Static).update(f"[{C['dim']}]No attack paths yet[/]")

            # Validation Status Panel
            v = self._validation_stats
            total_validated = v.get("validated", 0) + v.get("production_safe", 0)
            total_rejected = v.get("rejected", 0)
            total_pending = v.get("pending", 0)
            self.query_one("#validation", Static).update(
                f"[{C['dim']}]Validated[/]      [{C['green']}]{total_validated:>3d}[/]\n"
                f"[{C['dim']}]Prod-Safe[/]      [{C['cyan']}]{v.get('production_safe', 0):>3d}[/]\n"
                f"[{C['dim']}]Rejected[/]       [{C['red']}]{total_rejected:>3d}[/]\n"
                f"[{C['dim']}]Pending[/]        [{C['amber']}]{total_pending:>3d}[/]\n"
                f"[{C['dim']}]Mode[/]           [{C['green']}]STRICT[/]"
            )

            # Intelligence Panel
            learn_stats = self._learning.get_stats()
            hot_techs = learn_stats.get("hot_techniques", [])
            cold_techs = learn_stats.get("cold_techniques", [])
            learn_lines = [
                f"[{C['dim']}]Techniques[/]   {learn_stats.get('techniques_tracked', 0)}",
                f"[{C['dim']}]Tools[/]        {learn_stats.get('tools_tracked', 0)}",
                f"[{C['dim']}]Bypasses[/]     {learn_stats.get('bypass_patterns', 0)}",
            ]
            if hot_techs:
                learn_lines.append(f"[{C['green']}]Hot:[/] {hot_techs[0].get('technique', '')[:20]}")
            if cold_techs:
                learn_lines.append(f"[{C['red']}]Cold:[/] {cold_techs[0].get('technique', '')[:20]}")
            self.query_one("#intelligence", Static).update("\n".join(learn_lines))

            # Session Metrics
            self.query_one("#smetrics", Static).update(
                f"[{C['dim']}]Findings[/]           {self._findings_count:>5d}\n"
                f"[{C['dim']}]Vulnerabilities[/]    {self._severity_count(['critical', 'high', 'medium']):>5d}\n"
                f"[{C['dim']}]AI Categories[/]      {', '.join(self._ai_plan_categories)}\n"
                f"[{C['dim']}]Surface Cov[/]        [{C['green']}]{coverage}%[/]\n"
                f"[{C['dim']}]Threat Meter[/]       [{C['amber']}]■■■■■[/][{C['muted']}]■■■■■[/]\n"
                f"[{C['dim']}]Elapsed[/]            {elapsed // 60:02d}:{elapsed % 60:02d}"
            )
        except NoMatches:
            pass

    def _metric(self, name: str, pct: int, color: str) -> str:
        width = 18
        filled = max(0, min(width, pct * width // 100))
        return f"[{C['dim']}]{name:<6s}[/] [{color}]{'━' * filled}[/][{C['muted']}]{'━' * (width - filled)}[/] {pct}%"

    def _boot_real(self):
        output = self.query_one("#exec", RichLog)
        target = self.target
        output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['green']}]●[/] ARGUS Cockpit initialized for {target}")
        output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['cyan']}]🧠[/] AI Planning scan strategy...")
        think = self.query_one("#think", ThinkStream)
        think.add("[STATUS]", "Initializing real AI-powered pentest scan")
        think.add("[MODE]", f"Target: {target}")
        feed = self.query_one("#feed", ActivityFeed)
        feed.log("orch", "Cockpit         Real scan engine initializing...")

    async def _run_real_scan(self) -> None:
        output = self.query_one("#exec", RichLog)
        feed = self.query_one("#feed", ActivityFeed)
        think = self.query_one("#think", ThinkStream)
        graph = self.query_one("#graph", GraphViz)
        agents_widget = self.query_one("#agents", AgentTree)
        findings_widget = self.query_one("#find", FindSum)
        pipeline = self.query_one("#pipeline", PipelineView)

        from argus.agents.modes.pentest import PentestOrchestrator
        from argus.core.event_bus import get_event_bus
        from argus.core.events import (AgentStartedEvent, AgentCompletedEvent, AgentThinkingEvent,
                                       AgentProgressEvent, FindingDiscoveredEvent, ScanCompletedEvent)

        event_bus = get_event_bus()
        try:
            await event_bus.start()
        except Exception:
            pass

        # Subscribe to events for real-time updates
        @event_bus.subscribe("agent.started")
        async def on_agent_started(event: AgentStartedEvent):
            ts = datetime.now().strftime('%H:%M:%S')
            output.write(f"[{C['dim']}]{ts}[/] [{C['green']}]▶[/] {event.agent_name} started")
            feed.log("agent", f"{event.agent_name:<20s} started")
            agents_widget.set(event.agent_name, "running", 10, [], False)

        @event_bus.subscribe("agent.thinking")
        async def on_agent_thinking(event: AgentThinkingEvent):
            section = f"[{event.thought_type.upper()}]"
            think.add(section, event.thought[:120])
            agents_widget.set(event.agent_name, "running", 50, [event.thought_type], False)

        @event_bus.subscribe("agent.progress")
        async def on_agent_progress(event: AgentProgressEvent):
            ts = datetime.now().strftime('%H:%M:%S')
            pct = int(event.progress) if event.progress else 0
            agents_widget.set(event.agent_name, "running", pct, [event.message[:30]], True)

        @event_bus.subscribe("finding.discovered")
        async def on_finding(event: FindingDiscoveredEvent):
            ts = datetime.now().strftime('%H:%M:%S')
            severity_colors = {"critical": "red", "high": "amber", "medium": "yellow", "low": "green", "info": "cyan"}
            sc = severity_colors.get(event.severity.lower(), "white")
            output.write(f"[{C['dim']}]{ts}[/] [{C[sc]}][{event.severity.upper()}][/] {event.title}")
            feed.log("vuln", f"{event.title[:50]:50s}")
            findings_widget.add(event.title, event.severity, event.confidence)
            self._findings_count += 1
            graph.add(event.title[:30], self.target, "finding", event.severity, True)

            # XBOW: Register finding on attack surface
            self._surface.register(
                SurfaceCategory.ENDPOINT,
                f"finding:{event.title[:40]}",
                priority=0.8 if event.severity.lower() in ("critical", "high") else 0.4,
                tags=[event.severity, "finding"],
                parent=self.target,
            )

            # XBOW: Production-safe validation check
            f = Finding(title=event.title, description=event.description if hasattr(event, 'description') else "",
                       severity=event.severity, category="", evidence="")
            validation = self._validator.validate_exploit_safe(f)
            if validation.get("valid") and validation.get("confidence", 0) >= 0.7:
                self._validation_stats["production_safe"] += 1
            elif validation.get("safe") is False:
                self._validation_stats["rejected"] += 1
            else:
                self._validation_stats["pending"] += 1

        @event_bus.subscribe("scan.completed")
        async def on_scan_complete(event: ScanCompletedEvent):
            ts = datetime.now().strftime('%H:%M:%S')
            output.write(f"[{C['dim']}]{ts}[/] [{C['green']}]✅[/] Scan complete: {event.total_findings} findings in {event.duration:.1f}s")
            feed.log("orch", "Scan completed")
            self._scan_complete = True
            await event_bus.stop()

        pipeline.set_phase(1)
        await asyncio.sleep(0.5)

        # Create and run the real pentest orchestrator (AI plan + all agents)
        orchestrator = PentestOrchestrator(
            target=self.target,
            event_bus=event_bus,
            scan_depth="deep",
        )
        orchestrator.load_agents()

        # Run PlanAgent first to get AI plan
        plan_agent = orchestrator.agents[0]
        ts = datetime.now().strftime('%H:%M:%S')
        output.write(f"[{C['dim']}]{ts}[/] [{C['purple']}]🧠[/] AI Planning for {self.target}...")
        think.add("[AI PLANNING]", "Analyzing target to select optimal agents")
        pipeline.set_phase(1)
        agents_widget.set("AI Planner", "running", 30, ["analysis"], False)

        plan_result = await plan_agent.run()

        plan = (plan_result.metadata or {}).get("plan", {}) if hasattr(plan_result, "metadata") else {}
        if isinstance(plan, dict):
            self._ai_plan_categories = plan.get("categories", ["web", "api", "recon"])
            self._ai_plan_reason = plan.get("reason", "")
        output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['purple']}]🧠[/] AI Plan: {', '.join(self._ai_plan_categories)}")
        output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['purple']}]💡[/] Reasoning: {self._ai_plan_reason}")
        think.add("[AI PLAN]", f"Selected categories: {', '.join(self._ai_plan_categories)}")
        think.add("[REASONING]", self._ai_plan_reason)
        agents_widget.set("AI Planner", "completed", 100, list(self._ai_plan_categories), True)

        # Map agents to categories
        agent_cat_map = {
            "recon": "recon", "sqlinjection": "web", "xss": "web", "ssrf": "web",
            "commandinjection": "web", "authentication": "web", "idor": "web",
            "strixpentest": "web", "medusa": "web",
        }

        # Run ReconAgent (always)
        recon_agent = orchestrator.agents[1]
        ts = datetime.now().strftime('%H:%M:%S')
        output.write(f"[{C['dim']}]{ts}[/] [{C['cyan']}]🔍[/] Recon Agent starting...")
        feed.log("agent", "Recon Agent           Starting reconnaissance")
        agents_widget.set("Recon Agent", "running", 10, ["discovery"], False)
        pipeline.set_phase(2)

        # XBOW: Register target on attack surface
        self._surface.register(SurfaceCategory.DOMAIN, self.target, priority=1.0, tags=["primary", "target"])

        recon_result = await recon_agent.run()
        self._discovered_endpoints = list(dict.fromkeys(recon_result.metadata.get("endpoints", []) if hasattr(recon_result, "metadata") else []))
        self._discovered_technologies = list(dict.fromkeys(recon_result.metadata.get("technologies", []) if hasattr(recon_result, "metadata") else []))

        # XBOW: Register findings on attack surface
        for ep in self._discovered_endpoints[:20]:
            self._surface.register(SurfaceCategory.ENDPOINT, ep[:50], priority=0.6,
                                   parent=self.target, tags=["endpoint", "discovered"])
        for tech in self._discovered_technologies:
            self._surface.register(SurfaceCategory.TECHNOLOGY, tech[:50], priority=0.7,
                                   parent=self.target, tags=["technology", "detected"])

        if self._discovered_endpoints:
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['green']}]🌐[/] {len(self._discovered_endpoints)} endpoints discovered")
            feed.log("disc", f"Found {len(self._discovered_endpoints)} accessible endpoints")
        if self._discovered_technologies:
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['green']}]🖥️[/] Technologies: {', '.join(self._discovered_technologies[:5])}")
            feed.log("disc", f"Tech: {', '.join(self._discovered_technologies[:3])}")
            for tech in self._discovered_technologies:
                graph.add(tech, self.target, "tech", "detected", True)
        agents_widget.set("Recon Agent", "completed", 100, [f"{len(self._discovered_endpoints)} endpoints", f"{len(self._discovered_technologies)} tech"], True)

        # BackMeUp Agent — collect URLs from archives, filter root domain only
        from argus.toolkit.backmeup_agent import BackMeUpAgent
        custom_ports = []
        for ep in self._discovered_endpoints:
            try:
                p = urlparse(ep if "://" in ep else f"http://{ep}")
                if ":" in p.netloc:
                    port = int(p.netloc.split(":")[1])
                    if port not in [80, 443] and port not in custom_ports:
                        custom_ports.append(port)
            except Exception:
                pass
        backmeup = BackMeUpAgent(self.target, custom_ports=custom_ports, exclude_subs=True)
        ts = datetime.now().strftime('%H:%M:%S')
        output.write(f"[{C['dim']}]{ts}[/] [{C['cyan']}]📡[/] BackMeUp: collecting URLs for {self.target}...")
        feed.log("agent", "BackMeUp Agent        Collecting URLs from archives")
        agents_widget.set("BackMeUp", "running", 10, ["wayback", "gau", "katana"], False)
        think.add("[URL COLLECTION]", f"Collecting URLs for {self.target} from Wayback, Gau, CommonCrawl, OTX, URLScan...")

        bm_result = await backmeup.run()
        bm_urls = list(dict.fromkeys((bm_result.metadata or {}).get("collected_urls", []) if hasattr(bm_result, "metadata") else []))
        tool_stats = (bm_result.metadata or {}).get("tool_stats", {}) if hasattr(bm_result, "metadata") else {}

        if bm_urls:
            self._discovered_endpoints = list(dict.fromkeys(self._discovered_endpoints + bm_urls[:100]))
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['green']}]✅[/] BackMeUp: {len(bm_urls)} root-domain URLs collected")
            feed.log("disc", f"BackMeUp: {len(bm_urls)} URLs from archives")
            stats_str = ", ".join(f"{k}:{v}" for k, v in tool_stats.items() if v and v > 0)
            if stats_str:
                output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['cyan']}]📊[/] Tool stats: {stats_str}")
            think.add("[URL COLLECTION]", f"{len(bm_urls)} root-domain URLs collected. Passing to vulnerability scanners + skills.")
        else:
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['amber']}]⚠️[/] BackMeUp: no URLs found")
        agents_widget.set("BackMeUp", "completed", 100, [f"{len(bm_urls)} URLs"], True)

        # WAF Detection + AI Port Scanner (indices 2 and 3)
        waf_agent = orchestrator.agents[2]
        ts = datetime.now().strftime('%H:%M:%S')
        output.write(f"[{C['dim']}]{ts}[/] [{C['cyan']}]🛡️[/] WAF/Firewall Detection starting...")
        feed.log("agent", "WAF Detection          Analyzing firewall behavior")
        agents_widget.set("WAF Detection", "running", 30, ["waf_scan"], False)

        waf_result = await waf_agent.run()
        waf_meta = waf_result.metadata if hasattr(waf_result, "metadata") else {}
        detected_wafs = waf_meta.get("waf_detected", []) if isinstance(waf_meta, dict) else []
        nmap_flags = waf_meta.get("nmap_flags", "-sS -sV -sC -p- -T4") if isinstance(waf_meta, dict) else "-sS -sV -sC -p- -T4"

        if detected_wafs:
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['amber']}]🛡️[/] WAF Detected: {', '.join(detected_wafs)}")
            feed.log("vuln", f"WAF: {', '.join(detected_wafs)}")
            think.add("[WAF DETECTED]", f"Found: {', '.join(detected_wafs)}. Adjusting scan strategy.")
        else:
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['green']}]✅[/] No WAF detected")
            think.add("[WAF STATUS]", "No firewall detected, using aggressive scan")

        output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['cyan']}]🎯[/] AI selected Nmap flags: {nmap_flags}")
        agents_widget.set("WAF Detection", "completed", 100, [f"{len(detected_wafs)} WAFs"], True)
        think.add("[SCAN STRATEGY]", f"Nmap: {nmap_flags}")

        # AI Port Scanner — full port scan with Nmap
        from argus.agents.ai_port_scanner import AIPortScannerAgent
        port_scanner = AIPortScannerAgent(
            self.target, nmap_flags=nmap_flags, waf_detected=detected_wafs,
            event_bus=event_bus, memory_manager=None,
        )
        ts = datetime.now().strftime('%H:%M:%S')
        output.write(f"[{C['dim']}]{ts}[/] [{C['cyan']}]🔬[/] AI Port Scanner: nmap {nmap_flags} {self.target}")
        feed.log("agent", "AI Port Scanner       Full port scan with service detection")
        agents_widget.set("AI Port Scanner", "running", 10, ["nmap"], False)
        pipeline.set_phase(3)

        port_result = await port_scanner.run()
        open_ports = (port_result.metadata or {}).get("open_ports", []) if hasattr(port_result, "metadata") else []
        if open_ports:
            ports_str = ", ".join(f"{p['port']}/{p.get('service','?')}" for p in open_ports[:8])
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['green']}]✅[/] {len(open_ports)} open ports: {ports_str}")
            feed.log("disc", f"Found {len(open_ports)} open ports")
            for p in open_ports[:5]:
                graph.add(f"Port {p['port']}", self.target, "port", p.get('service', '?'), True)
                findings_widget.add(f"Port {p['port']}/{p.get('service','?')}", "info", 0.9)
        else:
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['amber']}]⚠️[/] No open ports found (firewall may be blocking)")
        agents_widget.set("AI Port Scanner", "completed", 100, [f"{len(open_ports)} ports"], True)

        # Run AI-selected vulnerability agents
        agents_widget.set("AI Selection", "running", 50, list(self._ai_plan_categories), False)
        feed.log("orch", f"AI selected agents for: {', '.join(self._ai_plan_categories)}")
        await asyncio.sleep(0.3)
        agents_widget.set("AI Selection", "completed", 100, list(self._ai_plan_categories), True)

        pipeline.set_phase(4)
        selected = []
        for agent in orchestrator.agents[4:]:  # Skip PlanAgent, WAF, ReconAgent, PortScanner
            key = agent.name.lower().replace(" ", "").replace("-", "").replace("_", "")
            cat = agent_cat_map.get(key, "")
            agent_name_lower = agent.name.lower()
            is_valid = False
            for plan_cat in self._ai_plan_categories:
                if plan_cat in agent_name_lower or cat == plan_cat or "poc" in agent_name_lower or "remediation" in agent_name_lower:
                    is_valid = True
                    break
            if is_valid or not agent_cat_map:
                selected.append(agent)
                agent.context = {"scan_id": orchestrator.scan_id, "target": self.target,
                                 "mode": "pentest", "shared_endpoints": self._discovered_endpoints,
                                 "shared_technologies": self._discovered_technologies}

        skipped = len(orchestrator.agents[2:]) - len(selected)
        if skipped > 0:
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['amber']}]🎯[/] AI skipped {skipped} irrelevant agents")

        for agent in selected:
            ts = datetime.now().strftime('%H:%M:%S')
            output.write(f"[{C['dim']}]{ts}[/] [{C['cyan']}]▶[/] {agent.name} executing...")
            feed.log("agent", f"{agent.name:<20s} launched")
            agents_widget.set(agent.name, "running", 10, [], False)
            try:
                result = await agent.run()
                ts = datetime.now().strftime('%H:%M:%S')
                output.write(f"[{C['dim']}]{ts}[/] [{C['green']}]✅[/] {agent.name} complete ({len(result.findings)} findings)")
                agents_widget.set(agent.name, "completed", 100, [f"{len(result.findings)} findings"], True)
                for f in result.findings:
                    findings_widget.add(f.title, f.severity, getattr(f, 'confidence', 1.0))
                    self._findings_count += 1
            except Exception as e:
                ts = datetime.now().strftime('%H:%M:%S')
                output.write(f"[{C['dim']}]{ts}[/] [{C['red']}]❌[/] {agent.name} failed: {e}")
                agents_widget.set(agent.name, "failed", 0, [str(e)[:30]], False)

        pipeline.set_phase(5)
        # XBOW: Auto-discover attack paths from findings
        output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['purple']}]🔗[/] Analyzing attack paths from findings...")
        feed.log("orch", "Chain analysis        Analyzing attack paths from findings")
        think.add("[ATTACK PATHS]", "Auto-discovering multi-step attack chains")
        agents_widget.set("Chain Analyzer", "running", 30, ["discovery"], False)

        from argus.core.chain_executor import get_chain_executor
        chain_exec = get_chain_executor(self.target)
        all_findings = []
        for agent in selected:
            if hasattr(agent, '_findings_to_validate'):
                all_findings.extend(agent._findings_to_validate)

        attack_paths = chain_exec.auto_discover_attack_paths(all_findings)
        self._attack_paths = [ap.to_dict() for ap in attack_paths]

        if attack_paths:
            output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['green']}]🔗[/] {len(attack_paths)} attack paths discovered")
            for ap in attack_paths[:3]:
                color = C["red"] if ap.severity == "critical" else C["amber"]
                output.write(f"  [{color}]▸[/] {ap.chain_name} [{C['dim']}]{ap.steps_completed}/{ap.total_steps} steps | {ap.confidence:.0%} conf[/]")
                feed.log("vuln", f"Attack path: {ap.chain_name[:40]}")

            # XBOW: Execute the highest-confidence chain
            top_path = attack_paths[0]
            if top_path.confidence >= 0.3:
                chain = None
                for c in CHAINS:
                    if c.name == top_path.chain_name:
                        chain = c
                        break
                if chain:
                    output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['amber']}]⚡[/] Executing chain: {chain.name}")
                    agents_widget.set(f"Chain: {chain.name[:20]}", "running", 30, [], False)
                    chain_result = await chain_exec.execute_chain(chain, all_findings)
                    agents_widget.set(f"Chain: {chain.name[:20]}", "completed", 100,
                                     [f"{chain_result.steps_completed}/{chain_result.total_steps}"], True)
                    output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [{C['green']}]✅[/] Chain result: {chain_result.steps_completed}/{chain_result.total_steps} steps")
                    feed.log("orch", f"Chain executed: {chain_result.steps_completed}/{chain_result.total_steps}")
                    self._learning.record_attack_path(
                        chain_name=chain.name, target=self.target,
                        steps_attempted=chain_result.total_steps,
                        steps_succeeded=chain_result.steps_completed,
                        total_duration=chain_result.findings_generated * 0.5,
                        findings_produced=chain_result.findings_generated,
                        success=chain_result.success,
                    )

        agents_widget.set("Chain Analyzer", "completed", 100, [f"{len(attack_paths)} paths"], True)

        # XBOW: Apply learning
        self._learning.persist()

        pipeline.set_phase(5)
        self._scan_complete = True
        ts = datetime.now().strftime('%H:%M:%S')
        output.write(f"[{C['dim']}]{ts}[/] [{C['green']}]✅[/] Scan complete: {self._findings_count} total findings")
        feed.log("orch", f"Scan finished: {self._findings_count} findings, {len(attack_paths)} attack paths")
        think.add("[COMPLETE]", f"Scan complete with {self._findings_count} findings. Press F2 to change mode.")

    def _blink_live(self) -> None:
        try:
            live = self.query_one("#live", Static)
            live.update(f"[{C['green']}]● LIVE[/]" if int(time.time() * 2) % 2 else f"[{C['dim']}]● LIVE[/]")
        except NoMatches:
            pass

    def _severity_count(self, names: List[str]) -> int:
        return sum(1 for _, severity, _, _ in self.query_one("#find", FindSum)._f if severity in names)

    def _hhmmss(self, offset: int) -> str:
        ts = datetime.fromtimestamp(self._t0 + offset)
        return ts.strftime("%H:%M:%S")

    def action_mode(self):
        self._mi = (self._mi + 1) % len(self._mk)
        self._theme = THEMES[self._mk[self._mi]]
        self._paint_bar()

    def action_cmd(self):
        try:
            self.query_one("#cmd", Input).focus()
        except NoMatches:
            pass

    def action_full(self):
        self.query_one("#main").toggle_class("full")

    def action_quit(self):
        self.push_screen(QuitModal())

    async def on_input_submitted(self, e):
        raw = e.value.strip()
        if not raw:
            return
        self.query_one("#cmd", Input).value = ""
        output = self.query_one("#exec", RichLog)
        output.write(f"[{C['dim']}]{datetime.now().strftime('%H:%M:%S')}[/] [bold]>[/] {raw}")
        self._commands += 1
        if not raw.startswith("/"):
            self.query_one("#think", ThinkStream).add("[OBJECTIVE]", raw)
            return

        parts = raw[1:].split()
        action = parts[0] if parts else ""
        if action == "help":
            output.write("  [bold]/graph[/] <q>  [bold]/scan[/] <target>  [bold]/chain[/] <finding>  [bold]/surface[/]  [bold]/learn[/]  [bold]/stats[/]  [bold]/mode[/]")
        elif action == "mode":
            self.action_mode()
            output.write(f"[{C['cyan']}]MODE[/] {self._theme['l']}")
        elif action == "graph" and len(parts) >= 2:
            query = " ".join(parts[1:])
            results = self._g.search_entities(query)
            output.write(f"[{C['purple']}]GRAPH[/] {len(results)} results")
            for entity in results[:5]:
                output.write(f"  {entity.type.value}  {entity.name}  [{C['dim']}]{entity.confidence:.0%}[/]")
        elif action == "chain" and len(parts) >= 2:
            query = " ".join(parts[1:])
            chains = find_matching_chains([query])
            if chains:
                output.write(f"[{C['amber']}]CHAIN[/] {len(chains)} matches")
                for chain in chains[:3]:
                    output.write(f"  {chain['chain']}")
            else:
                output.write(f"[{C['amber']}]CHAIN[/] none")
            if self._attack_paths:
                output.write(f"[{C['purple']}]ATTACK PATHS[/] {len(self._attack_paths)} discovered:")
                for ap in self._attack_paths[:5]:
                    output.write(f"  {ap.get('chain_name', '')} [{C['dim']}]{ap.get('steps_completed', 0)}/{ap.get('total_steps', 0)}[/]")
        elif action == "surface":
            surface_summary = self._surface.get_summary()
            output.write(f"[{C['cyan']}]SURFACE[/] {surface_summary.get('total_surface', 0)} items ({surface_summary.get('coverage_pct', 0)}% coverage)")
            pending = self._surface.get_pending(max_results=5)
            for p in pending:
                output.write(f"  [{C['amber']}]◌[/] {p.value[:40]:40s} [{C['dim']}]priority:{p.priority:.1f}[/]")
        elif action == "learn":
            learn_stats = self._learning.get_stats()
            output.write(f"[{C['purple']}]LEARN[/] {learn_stats.get('techniques_tracked', 0)} techniques, {learn_stats.get('tools_tracked', 0)} tools")
            for t in learn_stats.get("hot_techniques", [])[:3]:
                output.write(f"  [{C['green']}]HOT[/] {t.get('technique', '')} [{C['dim']}]reliability:{t.get('reliability', 0):.2f}[/]")
        elif action == "stats":
            stats = self._g.get_stats()
            surface_summary = self._surface.get_summary()
            output.write(
                f"[{C['cyan']}]STATS[/] {stats['total_entities']} entities  "
                f"{stats['total_relations']} relations  {len(self._g._feedback_history)} feedback"
            )
            output.write(
                f"[{C['cyan']}]SURFACE[/] {surface_summary.get('total_surface', 0)} items  "
                f"{surface_summary.get('explored', 0)} explored  "
                f"{len(self._attack_paths)} attack paths"
            )
        elif action == "scan" and len(parts) >= 2:
            self.target = parts[1]
            output.write(f"[{C['cyan']}]SCAN[/] retargeting cockpit to {self.target}")
            self.query_one("#pipeline", PipelineView).set_phase(0)
            self._paint_bar()
            self._paint_intel()
            asyncio.create_task(self._demo(parts[1], output))
        else:
            output.write(f"[{C['amber']}]UNKNOWN[/] use /help")

    async def _demo(self, target, output):
        think = self.query_one("#think", ThinkStream)
        agents = self.query_one("#agents", AgentTree)
        findings = self.query_one("#find", FindSum)
        graph = self.query_one("#graph", GraphViz)
        feed = self.query_one("#feed", ActivityFeed)
        pipeline = self.query_one("#pipeline", PipelineView)

        think.add("[TACTICAL PLAN]", f"Start controlled recon against {target}")
        agents.set("ReconAgent", "running", 30, ["Subfinder", "HTTPx", "ASN"])
        output.write(f"[{C['cyan']}]RECON[/] Enumerating {target}")
        feed.log("asset", "Subfinder           182 hosts discovered")
        await asyncio.sleep(0.4)

        pipeline.set_phase(1)
        graph.add(target, kind="host", detail="operator target", active=True)
        graph.add(f"api.{target}", target, "service", "443/tcp", True)
        graph.add("GraphQL", f"api.{target}", "app", "/graphql", True)
        think.add("[HYPOTHESIS]", "API subdomain exposes schema surface; verify before escalation")
        agents.set("ReconAgent", "running", 70, ["182 hosts"], sync=True)
        agents.set("ChainBuilder", "waiting")
        output.write(f"[{C['amber']}]CHAIN[/] GraphQL introspection -> object-level authorization review")
        findings.add("GraphQL introspection candidate", "high", 0.85, "graphql->object-auth")
        feed.log("vuln", "GraphQL candidate added to validation queue")
        await asyncio.sleep(0.4)

        pipeline.set_phase(2)
        agents.set("ReconAgent", "completed", 100, ["182 hosts"], True)
        agents.set("ChainBuilder", "completed", 100, ["2 chains"])
        think.add("[NEXT ACTION]", "Authenticated API fuzzing and authorization matrix build")
        output.write(f"[{C['green']}]Complete[/]")


def run_strix_cockpit(target=None):
    StrixCockpit(target=target).run()
