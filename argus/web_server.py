"""
Argus Web Dashboard Server — FastAPI + WebSocket backend.
Serves the React dashboard and bridges argus scan events to the browser.
"""

from __future__ import annotations

import asyncio
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from argus.core.logger import get_logger
from argus.core.event_bus import get_event_bus
from argus.core.di_container import get_container
from argus.core.session import SessionManager
from argus.agents.orchestrator import AgentOrchestrator

logger = get_logger()


def _append_log(logs: list, entry: dict) -> list:
    """Append log entry only if different from last, to avoid duplicates."""
    if logs and logs[-1].get("text") == entry.get("text") and logs[-1].get("agent_name") == entry.get("agent_name"):
        return logs
    logs.append(entry)
    return logs


# Current orchestrator reference for pause/kill
_current_orchestrator: Optional['AgentOrchestrator'] = None

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "web-dashboard" / "dist"


class ScanRequest(BaseModel):
    target: str
    mode: str = "pentest"


# ---- State manager ----
class DashboardState:
    """Tracks current scan state for WebSocket clients with disk persistence."""

    def __init__(self):
        self.session_mgr: Optional[SessionManager] = None
        self._session_dirty = False
        self.state: Dict[str, Any] = {
            "cpu": 0,
            "mem": 0,
            "net": 0,
            "tokens": 0,
            "maxTokens": 2000000,
            "credits": 5000,
            "uptime": "00:00:00",
            "llmModel": "",
            "sessionId": "",
            "time": "00:00:00",
            "target": "",
            "mode": "PENTEST",
            "agentStatus": "IDLE",
            "riskProfile": "Balanced",
            "maxParallel": "4 agents",
            "safeMode": True,
            "activeAgentName": "",
            "activeAgentTime": "00:00:00",
            "tokensUsed": "0k",
            "memoryPercent": 0,
            "knowledgeBase": "Idle",
            "agents": [],
            "pipeline": [
                {"name": "AI Planning", "completed": 0, "total": 1, "active": False},
                {"name": "Reconnaissance", "completed": 0, "total": 5, "active": False},
                {"name": "Enumeration", "completed": 0, "total": 3, "active": False},
                {"name": "Vulnerability", "completed": 0, "total": 4, "active": False},
                {"name": "AI Analysis", "completed": 0, "total": 2, "active": False},
                {"name": "Exploitation", "completed": 0, "total": 2, "active": False},
                {"name": "Reporting", "completed": 0, "total": 2, "active": False},
            ],
            "logs": [],
            "thinkingLines": [],
            "activities": [],
            "findings": [],
            "technologies": [],
            "discoveries": [],
            "nodes": [],
            "edges": [],
            "riskScore": 0,
            "riskLabel": "Unknown",
            "targetIP": "",
            "openPorts": 0,
            "subdomains": 0,
            "technologies_count": 0,
            "attackSurface": "Unknown",
            "commandsExecuted": 0,
            "dataCollected": "0 MB",
            "findingsCount": 0,
            "vulnerabilities": 0,
        }
        self.clients: Set[WebSocket] = set()
        self._start_time = time.time()

    def update(self, data: Dict[str, Any]):
        self.state.update(data)
        # Auto-add root node when target is set
        if data.get("target") and not self.state.get("nodes"):
            self.state["nodes"] = [{"id": "root", "label": data["target"], "x": 50, "y": 10, "type": "host", "color": "#00ff88"}]

    def _ensure_session(self) -> SessionManager:
        if self.session_mgr is None:
            self.session_mgr = SessionManager()
        return self.session_mgr

    def save_to_session(self):
        try:
            sm = self._ensure_session()
            state = self.state
            sm.save_session({
                "findings": state.get("findings", []),
                "agent_states": {a.get("name", ""): a.get("status", "") for a in state.get("agents", [])},
                "scan_progress": {
                    "pipeline": state.get("pipeline", []),
                    "technologies": state.get("technologies", []),
                    "discoveries": state.get("discoveries", []),
                    "nodes": state.get("nodes", []),
                    "edges": state.get("edges", []),
                },
                "chat_history": state.get("chat_history", []),
                "mode": state.get("mode", ""),
                "target": state.get("target", ""),
                "duration": state.get("duration", 0.0),
            })
            self._session_dirty = False
        except Exception as e:
            logger.debug(f"Session save error: {e}")

    def load_from_session(self, session_id: str) -> bool:
        try:
            sm = SessionManager()
            data = sm.load_session(session_id)
            if not data:
                return False
            findings = data.get("findings", [])
            scan_progress = data.get("scan_progress", {})
            pipeline = scan_progress.get("pipeline", [])
            nodes = scan_progress.get("nodes", [])
            edges = scan_progress.get("edges", [])
            technologies = scan_progress.get("technologies", [])
            discoveries = scan_progress.get("discoveries", [])
            self.state.update({
                "findings": findings,
                "findingsCount": len(findings),
                "pipeline": pipeline,
                "nodes": nodes,
                "edges": edges,
                "technologies": technologies,
                "technologies_count": len(technologies),
                "discoveries": discoveries,
                "mode": data.get("mode", "PENTEST"),
                "target": data.get("target", ""),
                "sessionId": session_id,
                "agentStatus": "IDLE",
                "chat_history": data.get("chat_history", []),
            })
            self.session_mgr = sm
            return True
        except Exception as e:
            logger.debug(f"Session load error: {e}")
            return False

    def get_state(self) -> Dict[str, Any]:
        elapsed = int(time.time() - self._start_time)
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        return {
            **self.state,
            "uptime": f"{h:02d}:{m:02d}:{s:02d}",
            "time": f"{h:02d}:{m:02d}:{s:02d}",
        }


dashboard_state = DashboardState()

# Pending scan from CLI (set by argus web -t before server starts)
_pending_scan: Optional[Dict[str, str]] = None


# ---- Event bus bridge ----
def setup_event_subscriptions():
    """Subscribe to argus EventBus and bridge to dashboard state."""
    bus = get_event_bus()

    @bus.subscribe("agent.started")
    async def on_agent_started(event):
        agents = dashboard_state.state.get("agents", [])
        now = datetime.now().strftime("%H:%M:%S")
        if not any(a.get("name") == event.agent_name for a in agents):
            agents.append({
                "name": event.agent_name,
                "id": event.agent_name.lower().replace(" ", "_"),
                "status": "running",
                "progress": 0,
                "findings": 0,
            })
        logs = dashboard_state.state.get("logs", [])
        logs = _append_log(logs, {"text": f"Agent started: {event.agent_name}", "type": "info", "timestamp": now, "agent_name": event.agent_name})
        activities = dashboard_state.state.get("activities", [])
        activities.append({"time": now, "agent": event.agent_name, "message": "Agent started"})
        dashboard_state.update({
            "activeAgentName": event.agent_name.upper(),
            "activeAgentTime": "00:00:00",
            "agentStatus": "EXECUTING",
            "agents": agents[-20:],
            "logs": logs[-50:],
            "activities": activities[-30:],
        })
        dashboard_state._session_dirty = True
        await broadcast_state()

    @bus.subscribe("agent.completed")
    async def on_agent_completed(event):
        agents = dashboard_state.state.get("agents", [])
        now = datetime.now().strftime("%H:%M:%S")
        for a in agents:
            if a["name"] == event.agent_name:
                a["status"] = "completed"
                a["progress"] = 100
        logs = dashboard_state.state.get("logs", [])
        logs = _append_log(logs, {"text": f"Agent completed: {event.agent_name} ({event.findings_count} findings)", "type": "success", "timestamp": now, "agent_name": event.agent_name})
        activities = dashboard_state.state.get("activities", [])
        activities.append({"time": now, "agent": event.agent_name, "message": f"Agent completed — {event.findings_count} findings"})
        dashboard_state.update({
            "agentStatus": "IDLE",
            "agents": agents,
            "logs": logs[-50:],
            "activities": activities[-30:],
        })
        dashboard_state._session_dirty = True
        await broadcast_state()

    @bus.subscribe("agent.failed")
    async def on_agent_failed(event):
        agents = dashboard_state.state.get("agents", [])
        now = datetime.now().strftime("%H:%M:%S")
        for a in agents:
            if a["name"] == event.agent_name:
                a["status"] = "error"
        logs = dashboard_state.state.get("logs", [])
        logs = _append_log(logs, {"text": f"Agent failed: {event.agent_name} — {event.error_message}", "type": "error", "timestamp": now, "agent_name": event.agent_name})
        activities = dashboard_state.state.get("activities", [])
        activities.append({"time": now, "agent": event.agent_name, "message": f"Agent failed: {event.error_message}"})
        dashboard_state.update({
            "agentStatus": "ERROR",
            "agents": agents,
            "logs": logs[-50:],
            "activities": activities[-30:],
        })
        await broadcast_state()

    @bus.subscribe("agent.thinking")
    async def on_agent_thinking(event):
        lines = dashboard_state.state.get("thinkingLines", [])
        lines = lines[-9:] + [f"> {event.thought}"]
        now = datetime.now().strftime("%H:%M:%S")
        logs = dashboard_state.state.get("logs", [])
        logs = _append_log(logs, {"text": f"[{event.agent_name}] {event.thought}", "type": "thinking", "timestamp": now, "agent_name": event.agent_name})
        dashboard_state.update({
            "thinkingLines": lines,
            "logs": logs[-50:],
        })
        await broadcast_state()

    @bus.subscribe("finding.discovered")
    async def on_finding(event):
        findings = dashboard_state.state.get("findings", [])
        now = datetime.now().strftime("%H:%M:%S")
        findings = findings[-19:] + [{
            "text": event.title,
            "title": event.title,
            "description": event.description,
            "severity": event.severity,
            "category": event.category,
            "evidence": event.evidence,
            "confidence": event.confidence,
            "cvss_score": event.cvss_score,
            "cwe_id": event.cwe_id,
            "remediation": event.remediation,
            "agent_name": event.agent_name,
        }]
        findings_count = dashboard_state.state.get("findingsCount", 0) + 1
        agents = dashboard_state.state.get("agents", [])
        for a in agents:
            if a["name"] == event.agent_name:
                a["findings"] = a.get("findings", 0) + 1
        logs = dashboard_state.state.get("logs", [])
        logs = _append_log(logs, {"text": f"Finding: {event.title} [{event.severity.upper()}]", "type": "warning", "timestamp": now, "agent_name": event.agent_name})

        # Extract technologies from findings (Recon Agent batch, httpx inline, or any tech finding)
        tech_update = {}
        existing_techs = dashboard_state.state.get("technologies", [])
        existing_names = {t.get("name") if isinstance(t, dict) else t for t in existing_techs}
        new_techs = []
        if event.agent_name == "Recon Agent" and "technologies" in event.title.lower():
            if event.evidence and event.evidence.startswith("Technologies:"):
                raw = event.evidence.replace("Technologies:", "").strip()
                tech_list = [t.strip() for t in raw.split(",") if t.strip()]
                for t in tech_list:
                    if t not in existing_names:
                        new_techs.append({"name": t, "icon": "", "percent": 100})
                        existing_names.add(t)
        elif event.agent_name == "httpx" and event.title.startswith("Technology: "):
            tech_name = event.title.replace("Technology: ", "").strip()
            if tech_name and tech_name not in existing_names:
                new_techs.append({"name": tech_name, "icon": "", "percent": 100})
                existing_names.add(tech_name)
        elif event.severity == "info" and event.category == "osint_tech" and "Technology" in event.title:
            tech_name = event.title.replace("Technology: ", "").strip() if "Technology:" in event.title else event.title.strip()
            if tech_name and tech_name not in existing_names:
                new_techs.append({"name": tech_name, "icon": "", "percent": 100})
                existing_names.add(tech_name)
        if new_techs:
            tech_update = {
                "technologies": existing_techs + new_techs,
                "technologies_count": len(existing_techs) + len(new_techs),
            }

        dashboard_state.update({
            "findings": findings,
            "findingsCount": findings_count,
            "agents": agents,
            "logs": logs[-50:],
            **tech_update,
        })
        dashboard_state._session_dirty = True
        await broadcast_state()

    @bus.subscribe("agent.progress")
    async def on_agent_progress(event):
        agents = dashboard_state.state.get("agents", [])
        now = datetime.now().strftime("%H:%M:%S")
        for a in agents:
            if a["name"] == event.agent_name:
                a["progress"] = max(a.get("progress", 0), int(event.progress))
        logs = dashboard_state.state.get("logs", [])
        if event.message:
            logs = _append_log(logs, {"text": f"[{event.agent_name}] {event.message}", "type": "info", "timestamp": now, "agent_name": event.agent_name})
        # Extract target IP from recon messages
        if event.message and "Target IP:" in event.message:
            import re as _re
            m = _re.search(r'Target IP:\s*([\d.]+)', event.message)
            if m:
                dashboard_state.update({"targetIP": m.group(1)})
        # Extract open ports from messages
        if event.message and "open ports:" in event.message.lower():
            import re as _re
            m = _re.search(r'open ports:\s*(\d+)', event.message, _re.I)
            if m:
                dashboard_state.update({"openPorts": int(m.group(1))})
        # Update pipeline stage from current_phase
        pipeline = list(dashboard_state.state.get("pipeline", []))
        phase_to_stage = {
            "planning": 0, "reconnaissance": 1, "enumeration": 2,
            "vulnerability": 3, "ai_analysis": 4, "exploitation": 5, "reporting": 6,
        }
        phase_agent_names = {
            "planning": "Plan Agent", "reconnaissance": "Recon Agent",
            "enumeration": "BackMeUp", "vulnerability": "Vuln Scanner",
            "ai_analysis": "Analysis Agent", "exploitation": "Exploitation Agent",
            "reporting": "Report Agent",
        }
        if event.current_phase == "completed":
            for s in pipeline:
                s["active"] = False
                s["completed"] = s["total"]
        elif event.current_phase in phase_to_stage:
            ix = phase_to_stage[event.current_phase]
            for i, s in enumerate(pipeline):
                was_active = s.get("active", False)
                is_current = i == ix
                if is_current and not was_active:
                    pipeline[i]["active"] = True
                elif not is_current and was_active and i < ix:
                    pipeline[i]["active"] = False
                    pipeline[i]["completed"] = pipeline[i]["total"]
            # Add phase agent to agents list if not already there
            agent_name = phase_agent_names.get(event.current_phase)
            if agent_name and not any(a.get("name") == agent_name for a in agents):
                agents.append({
                    "name": agent_name,
                    "id": agent_name.lower().replace(" ", "_"),
                    "status": "running" if pipeline[ix].get("active") else "idle",
                    "progress": int(event.progress),
                    "findings": 0,
                })
        # Update agent status based on pipeline
        for a in agents:
            a_name = a.get("name", "")
            a_phase = None
            for p_name, p_agent in phase_agent_names.items():
                if p_agent == a_name:
                    a_phase = p_name
                    break
            if a_phase and a_phase in phase_to_stage:
                ix = phase_to_stage[a_phase]
                s = pipeline[ix] if ix < len(pipeline) else None
                if s:
                    if s.get("completed") == s.get("total") and s.get("total", 0) > 0:
                        a["status"] = "completed"
                    elif s.get("active"):
                        a["status"] = "running"
                    else:
                        a["status"] = "idle"
        dashboard_state.update({
            "commandsExecuted": dashboard_state.state.get("commandsExecuted", 0) + 1,
            "dataCollected": f"{float(dashboard_state.state.get('dataCollected', '0').split()[0]) + 0.1:.1f} MB",
            "agents": agents,
            "logs": logs[-50:],
            "pipeline": pipeline,
        })
        await broadcast_state()


async def broadcast_state():
    """Broadcast current state to all connected WebSocket clients."""
    state = dashboard_state.get_state()
    msg = json.dumps({"type": "state", "payload": state})
    dead: List[WebSocket] = []
    for client in dashboard_state.clients:
        try:
            await client.send_text(msg)
        except Exception:
            dead.append(client)
    for d in dead:
        dashboard_state.clients.discard(d)


async def _auto_save_tick():
    """Periodically save dashboard state to session on disk."""
    while True:
        await asyncio.sleep(15)
        try:
            if dashboard_state._session_dirty:
                dashboard_state.save_to_session()
        except Exception:
            pass


async def _health_tick():
    """Periodically update system health metrics — live data."""
    import psutil
    from argus.agents.llm_client import get_cost_tracker, LLMClient
    from argus.core.config import get_config

    _prev_net = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    _prev_time = time.monotonic()

    while True:
        await asyncio.sleep(2)
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
        except Exception:
            cpu = 0
            mem = 0

        # Real network I/O rate
        try:
            now = time.monotonic()
            cur = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            elapsed = now - _prev_time
            net_rate = int((cur - _prev_net) / elapsed) if elapsed > 0 else 0
            _prev_net = cur
            _prev_time = now
        except Exception:
            net_rate = 0

        # Real token usage from CostTracker
        try:
            tokens = get_cost_tracker().total_tokens
        except Exception:
            tokens = dashboard_state.state.get("tokens", 0)

        # LLM status
        try:
            cfg = get_config()
            if cfg.has_ai_enabled:
                llm_model = LLMClient().model
            else:
                llm_model = "AI OFF"
        except Exception:
            llm_model = "AI OFF"

        dashboard_state.update({
            "cpu": round(cpu, 1),
            "mem": round(mem, 1),
            "net": net_rate,
            "tokens": tokens,
            "llmModel": llm_model,
        })
        if dashboard_state.clients:
            await broadcast_state()


# ---- FastAPI app ----
app = FastAPI(title="Argus Web Dashboard")


@app.on_event("startup")
async def startup():
    global _pending_scan
    bus = get_event_bus()
    await bus.start()
    setup_event_subscriptions()
    asyncio.create_task(_health_tick())
    asyncio.create_task(_auto_save_tick())

    # Load latest session from disk for persistence across restarts
    try:
        latest = SessionManager.get_latest_session()
        if latest:
            sid = latest.get("session_id", "")
            if sid:
                dashboard_state.load_from_session(sid)
                logger.info(f"Loaded last session: {sid} ({latest.get('target', 'unknown')})")
    except Exception as e:
        logger.debug(f"No previous session to load: {e}")

    # Start pending scan if set via CLI argus web -t
    if _pending_scan:
        ps = _pending_scan
        _pending_scan = None
        import re as _re
        target_ip = ps["target"] if _re.match(r'^\d+\.\d+\.\d+\.\d+$', ps["target"]) else ""
        dashboard_state.update({"targetIP": target_ip})
        await asyncio.sleep(1)
        await broadcast_state()
        asyncio.create_task(_run_scan_task(ps["target"], ps["mode"], ps["session_id"]))


@app.get("/api/state")
async def get_state():
    return dashboard_state.get_state()


@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    session_id = uuid.uuid4().hex[:8]
    import re as _re
    target_ip = req.target if _re.match(r'^\d+\.\d+\.\d+\.\d+$', req.target) else ""
    dashboard_state.update({
        "target": req.target,
        "mode": req.mode.upper(),
        "sessionId": session_id,
        "agentStatus": "PLANNING",
        "targetIP": target_ip,
        "commandsExecuted": 0,
        "dataCollected": "0 MB",
        "findingsCount": 0,
        "findings": [],
        "logs": [],
        "thinkingLines": [],
        "activities": [],
        "discoveries": [],
        "technologies": [],
        "technologies_count": 0,
    })
    await broadcast_state()

    asyncio.create_task(_run_scan_task(req.target, req.mode, session_id))

    return {"status": "started", "session_id": session_id}


async def _run_scan_task(target: str, mode: str, session_id: str):
    global _current_orchestrator
    try:
        from argus.core.config import set_config
        from argus.cli import run_scan as _run_scan
        set_config(verbose=False, output_dir=Path("./argus_results"))

        def _store_orchestrator(orch):
            global _current_orchestrator
            _current_orchestrator = orch

        result = await _run_scan(
            target=target,
            parallel=False,
            scan_depth="quick",
            non_interactive=True,
            mode=mode,
            event_bus=get_event_bus(),
            _from_web=True,
            _orchestrator_hook=_store_orchestrator,
        )

        findings_count = getattr(result, 'total_findings', 0)
        all_findings = getattr(result, 'all_findings', [])

        # Extract findings from result
        findings_list = []
        for f in all_findings:
            findings_list.append({
                "text": f.title,
                "title": f.title,
                "description": f.description,
                "severity": f.severity,
                "category": f.category,
                "evidence": f.evidence,
                "confidence": f.confidence,
                "cvss_score": f.cvss_score,
                "cwe_id": f.cwe_id,
                "remediation": f.remediation,
                "agent_name": f.agent_name,
            })

        # Extract agent results for nodes/edges
        agent_results = getattr(result, 'agent_results', [])
        nodes = dashboard_state.state.get("nodes", [])
        edges = dashboard_state.state.get("edges", [])
        if not nodes or (len(nodes) == 1 and nodes[0].get("id") == "root" and nodes[0].get("label") == "target.domain"):
            nodes = [{"id": "root", "label": target, "x": 50, "y": 10, "type": "host", "color": "#00ff88"}]

        logs = []
        activities = []
        for ar in agent_results:
            agent_name = getattr(ar, "agent_name", "unknown")
            logs = _append_log(logs, {"text": f"Agent {agent_name} completed — {len(getattr(ar, 'findings', []))} findings", "type": "info", "agent_name": agent_name})
            activities.append({"time": datetime.now().strftime("%H:%M:%S"), "agent": agent_name, "message": f"Agent completed with {len(getattr(ar, 'findings', []))} findings"})

            for f in getattr(ar, "findings", []):
                nid = f"f_{f.finding_id[:8] if hasattr(f, 'finding_id') and f.finding_id else 'unknown'}"
                if nid not in [n.get("id") for n in nodes]:
                    nodes.append({"id": nid, "label": f.title[:30], "sublabel": f.severity.upper(), "x": 30 + len(nodes) * 20, "y": 54, "type": "application", "color": "#a855f7"})
                    edges.append({"from": "root", "to": nid})

        dashboard_state.update({
            "findings": findings_list[-20:],
            "findingsCount": findings_count,
            "logs": (dashboard_state.state.get("logs", []) + logs)[-50:],
            "activities": (dashboard_state.state.get("activities", []) + activities)[-20:],
            "nodes": nodes,
            "edges": edges,
            "agentStatus": "IDLE",
        })
        await broadcast_state()
        logger.info(f"Scan completed: {target} — {findings_count} findings")
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        import traceback
        traceback.print_exc()
        dashboard_state.update({"agentStatus": "IDLE"})
        await broadcast_state()
    finally:
        global _current_orchestrator
        _current_orchestrator = None


@app.get("/api/scans")
async def list_scans():
    sessions = SessionManager.list_sessions()
    return {"scans": sessions}


@app.get("/api/scans/{session_id}")
async def load_scan(session_id: str):
    ok = dashboard_state.load_from_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    await broadcast_state()
    return {"status": "loaded", "session_id": session_id}


chat_history_store: List[Dict[str, Any]] = []


class ChatRequest(BaseModel):
    message: str


@app.get("/api/chat")
async def get_chat():
    return {"messages": chat_history_store[-50:]}


@app.post("/api/chat")
async def post_chat(req: ChatRequest):
    user_entry = {"role": "user", "text": req.message, "timestamp": datetime.now().isoformat(), "id": uuid.uuid4().hex[:8]}
    chat_history_store.append(user_entry)
    dashboard_state.state.setdefault("chat_history", []).append(user_entry)
    dashboard_state._session_dirty = True
    try:
        from argus.agents.llm_client import LLMClient
        client = LLMClient()
        system_prompt = "You are Argus AI, a cybersecurity assistant embedded in an autonomous pentesting dashboard. Answer concisely with security-relevant information."
        response = await client.generate(req.message, system=system_prompt, max_tokens=500, task="chat")
        reply_text = response.content if hasattr(response, 'content') else str(response)
        if not reply_text or reply_text.strip() == req.message:
            reply_text = "I'm analyzing the current scan state. For specific findings, check the Findings panel."
    except Exception:
        reply_text = "I'm processing your request. Check the scan progress for updates."
    reply_entry = {"role": "assistant", "text": str(reply_text)[:1000], "timestamp": datetime.now().isoformat(), "id": uuid.uuid4().hex[:8]}
    chat_history_store.append(reply_entry)
    dashboard_state.state.setdefault("chat_history", []).append(reply_entry)
    dashboard_state._session_dirty = True
    return {"reply": reply_entry["text"]}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    dashboard_state.clients.add(websocket)
    logger.info("WebSocket client connected")

    try:
        # Send initial state
        await websocket.send_text(json.dumps({
            "type": "state",
            "payload": dashboard_state.get_state(),
        }))

        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif msg.get("type") == "agent_pause":
                    agent_id = msg.get("payload", {}).get("agent_id", "")
                    agents = dashboard_state.state.get("agents", [])
                    matched_name = None
                    for a in agents:
                        if a.get("id") == agent_id or a.get("name", "").lower().replace(" ", "_") == agent_id:
                            a["status"] = "paused"
                            matched_name = a.get("name", "")
                            logger.info(f"Agent paused: {matched_name}")
                    dashboard_state.update({"agents": agents})
                    if matched_name and _current_orchestrator:
                        _current_orchestrator.pause_agent(matched_name)
                    await broadcast_state()
                elif msg.get("type") == "agent_resume":
                    agent_id = msg.get("payload", {}).get("agent_id", "")
                    agents = dashboard_state.state.get("agents", [])
                    matched_name = None
                    for a in agents:
                        if a.get("id") == agent_id or a.get("name", "").lower().replace(" ", "_") == agent_id:
                            a["status"] = "running"
                            matched_name = a.get("name", "")
                            logger.info(f"Agent resumed: {matched_name}")
                    dashboard_state.update({"agents": agents})
                    if matched_name and _current_orchestrator:
                        _current_orchestrator.resume_agent(matched_name)
                    await broadcast_state()
                elif msg.get("type") == "agent_kill":
                    agent_id = msg.get("payload", {}).get("agent_id", "")
                    agents = dashboard_state.state.get("agents", [])
                    matched_name = None
                    for a in agents:
                        if a.get("id") == agent_id or a.get("name", "").lower().replace(" ", "_") == agent_id:
                            a["status"] = "killed"
                            matched_name = a.get("name", "")
                            logger.info(f"Agent killed: {matched_name}")
                    dashboard_state.update({"agents": agents})
                    if matched_name and _current_orchestrator:
                        _current_orchestrator.cancel_agent(matched_name)
                    await broadcast_state()
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
    finally:
        dashboard_state.clients.discard(websocket)


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Serve index.html for all non-API routes (SPA fallback)."""
    index_path = DASHBOARD_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return JSONResponse({"error": "Dashboard not built"}, status_code=404)


# ---- Standalone runner ----
def run_server(host: str = "0.0.0.0", port: int = 8484):
    """Start the web dashboard server."""
    import uvicorn
    logger.info(f"Argus Web Dashboard: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
