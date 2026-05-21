"""
Interactive REPL Shell — power-user command-line interface for Argus.

Commands:
  graph query <entity>       Search entities
  graph path <a> <b>         Find paths between entities
  graph cluster <id>         Get entity cluster
  graph stats                Graph statistics

  scan <target> [--mode] [--depth]    Run ad-hoc scan
  scan list                           List active scans
  scan cancel <id>                    Cancel scan

  exploit <target> <type>    Run specific exploit (sqli/xss/nuclei)
  chain suggest <finding>    Get exploit chain suggestions

  feedback <finding_id> <correct/wrong>  Submit feedback
  learn stats                Learning engine statistics
  monitor add <target> [--interval]     Add monitoring target
  monitor list               List monitored targets
  monitor remove <target>    Remove monitor target

  export <format>            Export findings (json/sarif/md/html)
  help                       Show this help
  exit                       Exit REPL
"""

import asyncio
import cmd
import json
import shlex
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from argus.core.logger import get_logger
from argus.core.graph_memory import GraphMemory, EntityType, get_graph_memory
from argus.core.chain_matrix import find_matching_chains, get_next_suggestions
from argus.core.learning_engine import get_learning_engine
from argus.core.monitor import get_monitor
from argus.core.report_generator import ReportGenerator
from argus.agents.base_agent import Finding

logger = get_logger()


class ArgusREPL(cmd.Cmd):
    prompt = "argus> "
    intro = """
    ╔══════════════════════════════════════════╗
    ║         Argus Interactive Shell          ║
    ║  Type 'help' for commands, 'exit' to quit ║
    ╚══════════════════════════════════════════╝
    """

    def __init__(self, graph: Optional[GraphMemory] = None):
        super().__init__()
        self._graph = graph or get_graph_memory()
        self._learn = get_learning_engine()
        self._monitor = get_monitor()

    # ─── Graph Commands ───────────────────────────────────────────────
    def do_graph(self, arg):
        """graph query/path/cluster/stats <args>"""
        args = shlex.split(arg)
        if not args:
            print("Usage: graph query|path|cluster|stats")
            return
        sub = args[0]
        if sub == "query" and len(args) >= 2:
            q = " ".join(args[1:])
            results = self._graph.search_entities(q)
            print(f"\nFound {len(results)} results for '{q}':")
            for e in results[:20]:
                print(f"  [{e.type.value:15s}] {e.name:40s} conf={e.confidence:.2f}")
        elif sub == "path" and len(args) >= 3:
            paths = self._graph.find_paths(args[1], args[2])
            print(f"\nFound {len(paths)} paths:")
            for i, path in enumerate(paths[:3]):
                print(f"  Path {i+1}: {' → '.join(p['entity']['name'] for p in path)}")
        elif sub == "cluster" and len(args) >= 2:
            cluster = self._graph.get_cluster(args[1])
            print(f"\nCluster: {cluster['entity_count']} entities, {cluster['relation_count']} relations")
            for name, entity in list(cluster.get("entities", {}).items())[:10]:
                print(f"  {name}")
        elif sub == "stats":
            stats = self._graph.get_stats()
            print(f"\nGraph Memory Stats:")
            for k, v in stats.items():
                print(f"  {k}: {v}")
        else:
            print("Usage: graph query|path|cluster|stats")

    # ─── Scan Commands ────────────────────────────────────────────────
    def do_scan(self, arg):
        """scan <target> [--mode pentest] [--depth quick]"""
        args = shlex.split(arg)
        if not args:
            print("Usage: scan <target> [--mode pentest/osint/ctf] [--depth quick/standard/deep]")
            return
        if args[0] == "list":
            print("Active scans: (use REST API for tracking)")
            return
        target = args[0]
        mode = "pentest"
        depth = "quick"
        for i, a in enumerate(args):
            if a == "--mode" and i + 1 < len(args):
                mode = args[i + 1]
            if a == "--depth" and i + 1 < len(args):
                depth = args[i + 1]
        print(f"Starting {mode} scan on {target} (depth={depth})...")
        asyncio.ensure_future(self._run_scan_async(target, mode, depth))
        print("Scan started in background")

    async def _run_scan_async(self, target, mode, depth):
        from argus.agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator(target=target, mode=mode, scan_depth=depth)
        orch.add_default_agents()
        result = await orch.run()
        print(f"\nScan complete: {result.total_findings} findings")
        sev_counts = result.findings_by_severity
        for sev in ["critical", "high", "medium", "low", "info"]:
            if sev_counts.get(sev, 0) > 0:
                print(f"  {sev.upper()}: {sev_counts[sev]}")

    # ─── Exploit Commands ─────────────────────────────────────────────
    def do_exploit(self, arg):
        """exploit <target> <type>"""
        args = shlex.split(arg)
        if len(args) < 2:
            print("Usage: exploit <target> <type> (sqli/xss/nuclei/ssrf)")
            return
        print(f"Running {args[1]} exploit against {args[0]}...")
        print("Use REST API for async exploit execution")

    # ─── Chain Commands ───────────────────────────────────────────────
    def do_chain(self, arg):
        """chain suggest <finding>"""
        args = shlex.split(arg)
        if len(args) < 2 or args[0] != "suggest":
            print("Usage: chain suggest <finding>")
            return
        suggestions = get_next_suggestions([" ".join(args[1:])])
        if suggestions:
            print(f"\nFound {len(suggestions)} chain suggestions:")
            for s in suggestions[:5]:
                print(f"  [{s['chain'][:40]:40s}] → {s['next_step']}")
        else:
            print("No chain suggestions found")

    # ─── Feedback Commands ────────────────────────────────────────────
    def do_feedback(self, arg):
        """feedback <finding_id> <correct|wrong>"""
        args = shlex.split(arg)
        if len(args) < 2:
            print("Usage: feedback <finding_id> <correct|wrong>")
            return
        positive = args[1].lower() in ("correct", "true", "yes", "1")
        self._graph.give_feedback(args[0], positive=positive, amount=0.3, source="repl")
        print(f"Feedback recorded: {args[0]} → {'positive' if positive else 'negative'}")

    # ─── Learning Commands ────────────────────────────────────────────
    def do_learn(self, arg):
        """learn stats"""
        args = shlex.split(arg)
        if args and args[0] == "stats":
            stats = self._learn.get_stats()
            print(f"\nLearning Engine Stats:")
            print(f"  Techniques tracked: {stats['techniques_tracked']}")
            print(f"  Tools tracked: {stats['tools_tracked']}")
            print(f"  Bypass patterns: {stats['bypass_patterns']}")
            if stats.get("top_techniques"):
                print(f"\n  Top Techniques:")
                for t in stats["top_techniques"][:5]:
                    print(f"    {t['technique']} on {t['target_tech']}: {t['success_rate']:.0%} success")
        else:
            print("Usage: learn stats")

    # ─── Monitor Commands ─────────────────────────────────────────────
    def do_monitor(self, arg):
        """monitor add/list/remove <args>"""
        args = shlex.split(arg)
        if not args:
            print("Usage: monitor add|list|remove")
            return
        sub = args[0]
        if sub == "add" and len(args) >= 2:
            interval = 24
            for i, a in enumerate(args):
                if a == "--interval" and i + 1 < len(args):
                    interval = float(args[i + 1])
            self._monitor.add_target(args[1], interval_hours=interval)
            print(f"Added {args[1]} to monitoring (every {interval}h)")
        elif sub == "list":
            targets = self._monitor.list_targets()
            if targets:
                print(f"\nMonitored targets ({len(targets)}):")
                for t in targets:
                    print(f"  {t['target']:40s} interval={t['interval_hours']}h mode={t['mode']}")
            else:
                print("No monitored targets")
        elif sub == "remove" and len(args) >= 2:
            if self._monitor.remove_target(args[1]):
                print(f"Removed {args[1]} from monitoring")
            else:
                print(f"Target {args[1]} not found")
        else:
            print("Usage: monitor add|list|remove")

    # ─── Export Commands ──────────────────────────────────────────────
    def do_export(self, arg):
        """export <format> (json/sarif/md/html)"""
        fmt = arg.strip() or "json"
        print(f"Exporting to {fmt}...")
        print("Use REST API: GET /scans/:id/report/:format")

    # ─── System Commands ──────────────────────────────────────────────
    def do_help(self, arg):
        """Show available commands"""
        print("""
Commands:
  graph query|path|cluster|stats    Graph memory operations
  scan <target> [--mode] [--depth]  Run ad-hoc scan
  exploit <target> <type>           Run exploit
  chain suggest <finding>           Exploit chain suggestions
  feedback <id> <correct|wrong>     Submit feedback
  learn stats                       Learning engine status
  monitor add|list|remove           Continuous monitoring
  export <format>                   Export findings
  help                              This help
  exit                              Exit REPL
        """)

    def do_exit(self, arg):
        """Exit the REPL"""
        print("Goodbye!")
        self._learn.persist()
        return True

    def do_EOF(self, arg):
        return self.do_exit(arg)

    def default(self, line):
        print(f"Unknown command: {line}. Type 'help' for available commands.")


def start_repl(graph: Optional[GraphMemory] = None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    repl = ArgusREPL(graph)
    repl.cmdloop()
