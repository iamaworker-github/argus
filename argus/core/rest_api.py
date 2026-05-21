"""
REST API Server — FastAPI-based REST API for Argus.

Endpoints:
  GET    /health                    Health check
  POST   /scans                     Start a new scan
  GET    /scans                     List all scans
  GET    /scans/:id                 Get scan status/details
  POST   /scans/:id/cancel          Cancel a scan
  GET    /scans/:id/findings        Get findings for a scan
  GET    /scans/:id/report/:format  Download report (json/sarif/md/html)

  GET    /graph/entities            List graph entities
  GET    /graph/entities/search     Search entities
  GET    /graph/entities/:id        Get entity details
  GET    /graph/relationships       List relationships
  GET    /graph/paths               Find paths between entities
  GET    /graph/cluster/:id         Get entity cluster

  POST   /feedback                  Submit human feedback on findings
  GET    /stats                     Overall system stats
  GET    /tools                     List available tools
  POST   /tools/:name/execute       Execute a tool ad-hoc

  POST   /notify/channels           Add notification channel
  GET    /notify/channels           List notification channels
  DELETE /notify/channels/:name     Remove notification channel

  GET    /ws                        WebSocket endpoint
"""

import asyncio
import json
import time
import uuid
from typing import Optional, Dict, Any, List
from pathlib import Path

from argus.core.logger import get_logger
from argus.core.graph_memory import GraphMemory, EntityType, Entity, get_graph_memory
from argus.core.session import SessionManager
from argus.core.report_generator import ReportGenerator
from argus.core.notifier import Notifier, get_notifier, NotificationChannel
from argus.core.config import get_config
from argus.core.blackboard import get_blackboard

logger = get_logger()
config = get_config()

try:
    from fastapi import FastAPI, HTTPException, Query, Body, Path as FPath
    from fastapi.responses import JSONResponse, PlainTextResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class RESTAPI:
    """FastAPI-based REST API server for Argus."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8484,
                 graph: Optional[GraphMemory] = None):
        self.host = host
        self.port = port
        self._graph = graph or get_graph_memory()
        self._server = None
        self._running = False
        self._active_scans: Dict[str, dict] = {}
        self._app = None

    def build_app(self):
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI not installed. Install with: pip install fastapi uvicorn")
            return

        app = FastAPI(title="Argus REST API", version="2.0.0",
                      description="AI-Powered Security Testing Platform API")

        # ─── Health ─────────────────────────────────────────────────────
        @app.get("/health")
        async def health():
            return {"status": "ok", "timestamp": time.time(), "version": "2.0.0"}

        # ─── Scans ──────────────────────────────────────────────────────
        @app.post("/scans")
        async def start_scan(target: str = Body(embed=True),
                             mode: str = Body("pentest"),
                             depth: str = Body("deep"),
                             instruction: Optional[str] = Body(None)):
            scan_id = str(uuid.uuid4())
            self._active_scans[scan_id] = {
                "id": scan_id, "target": target, "mode": mode,
                "depth": depth, "status": "queued",
                "created_at": time.time(), "findings": [],
            }
            asyncio.create_task(self._run_scan_background(scan_id, target, mode, depth, instruction))
            return {"scan_id": scan_id, "status": "queued", "target": target}

        @app.get("/scans")
        async def list_scans():
            return {"scans": list(self._active_scans.values())}

        @app.get("/scans/{scan_id}")
        async def get_scan(scan_id: str):
            scan = self._active_scans.get(scan_id)
            if not scan:
                raise HTTPException(404, "Scan not found")
            return scan

        @app.post("/scans/{scan_id}/cancel")
        async def cancel_scan(scan_id: str):
            scan = self._active_scans.get(scan_id)
            if not scan:
                raise HTTPException(404, "Scan not found")
            scan["status"] = "cancelled"
            return {"scan_id": scan_id, "status": "cancelled"}

        @app.get("/scans/{scan_id}/findings")
        async def get_findings(scan_id: str,
                               severity: Optional[str] = Query(None),
                               limit: int = Query(100)):
            scan = self._active_scans.get(scan_id)
            if not scan:
                raise HTTPException(404, "Scan not found")
            findings = scan.get("findings", [])
            if severity:
                findings = [f for f in findings if f.get("severity") == severity]
            return {"scan_id": scan_id, "total": len(findings), "findings": findings[:limit]}

        @app.get("/scans/{scan_id}/report/{fmt}")
        async def get_report(scan_id: str, fmt: str):
            scan = self._active_scans.get(scan_id)
            if not scan:
                raise HTTPException(404, "Scan not found")
            from argus.agents.base_agent import Finding
            findings = [Finding(**f) if isinstance(f, dict) else f for f in scan.get("findings", [])]
            gen = ReportGenerator()
            fmt = fmt.lower()
            if fmt == "json":
                return gen.generate_sarif(findings, scan["target"])
            elif fmt == "md":
                return PlainTextResponse(gen.generate_markdown(findings, scan["target"]))
            elif fmt == "html":
                return PlainTextResponse(gen.generate_html(findings, scan["target"]))
            raise HTTPException(400, f"Unsupported format: {fmt}")

        # ─── Graph ──────────────────────────────────────────────────────
        @app.get("/graph/entities")
        async def list_entities(type_filter: Optional[str] = Query(None, alias="type"),
                                 tag: Optional[str] = Query(None),
                                 limit: int = Query(100)):
            if type_filter:
                try:
                    etype = EntityType(type_filter)
                    entities = self._graph.find_entity(etype=etype)
                except ValueError:
                    entities = self._graph.search_entities(type_filter)
            elif tag:
                entities = self._graph.find_entity(tag=tag)
            else:
                entities = list(self._graph._entities.values())[:limit]
            return {"total": len(entities), "entities": [e.to_dict() for e in entities[:limit]]}

        @app.get("/graph/entities/search")
        async def search_entities(q: str = Query(), limit: int = Query(20)):
            results = self._graph.search_entities(q, limit=limit)
            return {"query": q, "total": len(results), "entities": [e.to_dict() for e in results]}

        @app.get("/graph/entities/{entity_id}")
        async def get_entity(entity_id: str):
            entity = self._graph.get_entity(entity_id)
            if not entity:
                raise HTTPException(404, "Entity not found")
            rels = self._graph.get_relations(entity_id)
            return {
                "entity": entity.to_dict(),
                "relationships": [r.to_dict() for r in rels],
            }

        @app.get("/graph/relationships")
        async def list_relationships(entity_id: Optional[str] = Query(None),
                                      type_filter: Optional[str] = Query(None, alias="type"),
                                      limit: int = Query(100)):
            if entity_id:
                rels = self._graph.get_relations(entity_id)
            else:
                rels = list(self._graph._relationships.values())[:limit]
            return {"total": len(rels), "relationships": [r.to_dict() for r in rels[:limit]]}

        @app.get("/graph/paths")
        async def find_paths(source: str = Query(), target: str = Query(),
                              max_depth: int = Query(5)):
            paths = self._graph.find_paths(source, target, max_depth=max_depth)
            return {"source": source, "target": target, "paths": paths}

        @app.get("/graph/cluster/{entity_id}")
        async def get_cluster(entity_id: str, max_entities: int = Query(50)):
            cluster = self._graph.get_cluster(entity_id, max_entities=max_entities)
            return cluster

        # ─── Feedback ───────────────────────────────────────────────────
        @app.post("/feedback")
        async def submit_feedback(finding_id: str = Body(embed=True),
                                   correct: bool = Body(True),
                                   source: str = Body("human")):
            self._graph.give_feedback(finding_id, positive=correct, amount=0.3, source=source)
            return {"status": "ok", "finding_id": finding_id, "feedback": "positive" if correct else "negative"}

        # ─── Stats ──────────────────────────────────────────────────────
        @app.get("/stats")
        async def get_stats():
            graph_stats = self._graph.get_stats()
            return {
                "graph": graph_stats,
                "active_scans": len(self._active_scans),
                "api_version": "2.0.0",
            }

        # ─── Tools ──────────────────────────────────────────────────────
        @app.get("/tools")
        async def list_tools():
            return {"tools": ["nmap", "nuclei", "httpx", "naabu", "subfinder", "ffuf", "sqlmap"]}

        # ─── Notification Channels ──────────────────────────────────────
        @app.post("/notify/channels")
        async def add_channel(name: str = Body(embed=True),
                               type: str = Body(embed=True),
                               webhook_url: str = Body(embed=True),
                               min_severity: str = Body("high")):
            notifier = get_notifier()
            channel = NotificationChannel(name=name, type=type,
                                          config={"webhook_url": webhook_url},
                                          min_severity=min_severity)
            notifier.add_channel(channel)
            return {"status": "ok", "name": name, "type": type}

        @app.get("/notify/channels")
        async def list_channels():
            return {"channels": get_notifier().list_channels()}

        @app.delete("/notify/channels/{name}")
        async def remove_channel(name: str):
            notifier = get_notifier()
            if notifier.remove_channel(name):
                return {"status": "ok", "name": name}
            raise HTTPException(404, "Channel not found")

        self._app = app
        return app

    async def start(self):
        if not FASTAPI_AVAILABLE:
            logger.warning("Install fastapi+uvicorn: pip install fastapi uvicorn")
            return
        if not self._app:
            self.build_app()
        self._running = True
        cfg = uvicorn.Config(self._app, host=self.host, port=self.port, log_level="warning")
        self._server = uvicorn.Server(cfg)
        logger.info(f"REST API server starting on http://{self.host}:{self.port}")
        await self._server.serve()

    async def stop(self):
        self._running = False
        if self._server:
            self._server.should_exit = True

    async def _run_scan_background(self, scan_id: str, target: str, mode: str,
                                    depth: str, instruction: Optional[str]):
        scan = self._active_scans.get(scan_id)
        if not scan:
            return
        scan["status"] = "running"
        scan["started_at"] = time.time()
        try:
            from argus.agents.orchestrator import AgentOrchestrator
            orch = AgentOrchestrator(target=target, mode=mode, scan_depth=depth,
                                     instruction=instruction)
            orch.add_default_agents()
            result = await orch.run()
            scan["findings"] = [f.to_dict() for f in result.all_findings]
            scan["status"] = "completed"
            scan["completed_at"] = time.time()
            scan["summary"] = {
                "total_findings": result.total_findings,
                "severity": result.findings_by_severity,
                "duration": result.duration,
            }
        except Exception as e:
            scan["status"] = "failed"
            scan["error"] = str(e)
            logger.error(f"Scan {scan_id} failed: {e}")


def create_api() -> Optional[RESTAPI]:
    if not FASTAPI_AVAILABLE:
        return None
    return RESTAPI()
