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
from argus.agents.orchestrator import AgentOrchestrator

logger = get_logger()

# Current orchestrator reference for pause/kill
_current_orchestrator: Optional['AgentOrchestrator'] = None

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "web-dashboard" / "dist"


class ScanRequest(BaseModel):
    target: str
    mode: str = "pentest"


# ---- State manager ----
class DashboardState:
    """Tracks current scan state for WebSocket clients."""

    def __init__(self):
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
                {"name": "Reconnaissance", "completed": 0, "total": 4, "active": False},
                {"name": "Enumeration", "completed": 0, "total": 4, "active": False},
                {"name": "Analysis", "completed": 0, "total": 3, "active": False},
                {"name": "Vulnerability", "completed": 0, "total": 4, "active": False},
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
        logs.append({"text": f"Agent started: {event.agent_name}", "type": "info", "timestamp": now, "agent_name": event.agent_name})
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
        logs.append({"text": f"Agent completed: {event.agent_name} ({event.findings_count} findings)", "type": "success", "timestamp": now, "agent_name": event.agent_name})
        activities = dashboard_state.state.get("activities", [])
        activities.append({"time": now, "agent": event.agent_name, "message": f"Agent completed — {event.findings_count} findings"})
        dashboard_state.update({
            "agentStatus": "IDLE",
            "agents": agents,
            "logs": logs[-50:],
            "activities": activities[-30:],
        })
        await broadcast_state()

    @bus.subscribe("agent.failed")
    async def on_agent_failed(event):
        agents = dashboard_state.state.get("agents", [])
        now = datetime.now().strftime("%H:%M:%S")
        for a in agents:
            if a["name"] == event.agent_name:
                a["status"] = "error"
        logs = dashboard_state.state.get("logs", [])
        logs.append({"text": f"Agent failed: {event.agent_name} — {event.error_message}", "type": "error", "timestamp": now, "agent_name": event.agent_name})
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
        logs.append({"text": f"[{event.agent_name}] {event.thought}", "type": "thinking", "timestamp": now, "agent_name": event.agent_name})
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
        logs.append({"text": f"Finding: {event.title} [{event.severity.upper()}]", "type": "warning", "timestamp": now, "agent_name": event.agent_name})
        dashboard_state.update({
            "findings": findings,
            "findingsCount": findings_count,
            "agents": agents,
            "logs": logs[-50:],
        })
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
            logs.append({"text": f"[{event.agent_name}] {event.message}", "type": "info", "timestamp": now, "agent_name": event.agent_name})
        dashboard_state.update({
            "commandsExecuted": dashboard_state.state.get("commandsExecuted", 0) + 1,
            "dataCollected": f"{float(dashboard_state.state.get('dataCollected', '0').split()[0]) + 0.1:.1f} MB",
            "agents": agents,
            "logs": logs[-50:],
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

    # Start pending scan if set via CLI argus web -t
    if _pending_scan:
        ps = _pending_scan
        _pending_scan = None
        await asyncio.sleep(1)
        await broadcast_state()
        asyncio.create_task(_run_scan_task(ps["target"], ps["mode"], ps["session_id"]))


@app.get("/api/state")
async def get_state():
    return dashboard_state.get_state()


@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    session_id = uuid.uuid4().hex[:8]
    dashboard_state.update({
        "target": req.target,
        "mode": req.mode.upper(),
        "sessionId": session_id,
        "agentStatus": "PLANNING",
        "commandsExecuted": 0,
        "dataCollected": "0 MB",
        "findingsCount": 0,
        "findings": [],
        "logs": [],
        "thinkingLines": [],
        "activities": [],
        "discoveries": [],
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
            logs.append({"text": f"Agent {agent_name} completed — {len(getattr(ar, 'findings', []))} findings", "type": "info", "agent_name": agent_name})
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
    return {"scans": []}


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
