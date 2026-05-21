"""
WebSocket Real-Time External API — streams scan progress, findings, and agent status
to connected external clients in real-time.
"""

import asyncio
import json
import time
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field

from argus.core.logger import get_logger
from argus.core.event_bus import get_event_bus

logger = get_logger()


@dataclass
class WSClient:
    websocket: Any
    client_id: str
    connected_at: float = field(default_factory=time.time)
    filters: Dict[str, Any] = field(default_factory=dict)


class WebSocketAPI:
    """WebSocket server that streams real-time scan events to external clients."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._clients: Dict[str, WSClient] = {}
        self._server: Optional[Any] = None
        self._subscribed = False
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._subscribe_to_events()
        try:
            import websockets
            self._server = await websockets.serve(
                self._handle_client, self.host, self.port,
                max_size=2 ** 20,  # 1 MB max message
            )
            logger.info(f"WebSocket API server started on ws://{self.host}:{self.port}")
        except ImportError:
            logger.warning("websockets not installed. WebSocket API disabled.")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")

    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        for client in list(self._clients.values()):
            await self._disconnect_client(client)
        logger.info("WebSocket API server stopped")

    async def broadcast(self, event_type: str, data: dict):
        message = json.dumps({"type": event_type, "data": data, "timestamp": time.time()})
        dead_clients = []
        for client_id, client in self._clients.items():
            try:
                await client.websocket.send(message)
            except Exception:
                dead_clients.append(client_id)
        for cid in dead_clients:
            self._clients.pop(cid, None)

    async def _handle_client(self, websocket):
        client_id = f"client_{int(time.time() * 1000)}_{len(self._clients)}"
        client = WSClient(websocket=websocket, client_id=client_id)
        self._clients[client_id] = client
        logger.info(f"WebSocket client connected: {client_id} (total: {len(self._clients)})")

        try:
            async for raw_message in websocket:
                try:
                    msg = json.loads(raw_message)
                    await self._handle_message(client, msg)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON"}))
        except Exception:
            pass
        finally:
            await self._disconnect_client(client)

    async def _disconnect_client(self, client: WSClient):
        self._clients.pop(client.client_id, None)
        try:
            await client.websocket.close()
        except Exception:
            pass
        logger.info(f"WebSocket client disconnected: {client.client_id}")

    async def _handle_message(self, client: WSClient, msg: dict):
        action = msg.get("action", "")
        if action == "ping":
            await client.websocket.send(json.dumps({"type": "pong"}))
        elif action == "subscribe":
            client.filters = msg.get("filters", {})
            await client.websocket.send(json.dumps({"type": "subscribed", "filters": client.filters}))
        elif action == "list_clients":
            await client.websocket.send(json.dumps({
                "type": "clients",
                "data": {"count": len(self._clients), "clients": list(self._clients.keys())},
            }))

    def _subscribe_to_events(self):
        if self._subscribed:
            return
        bus = get_event_bus()

        @bus.subscribe("finding.discovered")
        async def on_finding(event):
            await self.broadcast("finding.discovered", {
                "title": getattr(event, "title", ""),
                "severity": getattr(event, "severity", ""),
                "target": getattr(event, "target", ""),
                "description": getattr(event, "description", ""),
            })

        @bus.subscribe("agent.*")
        async def on_agent_event(event):
            await self.broadcast(event.event_type, {
                "agent_name": getattr(event, "agent_name", ""),
                "status": getattr(event, "status", ""),
                "target": getattr(event, "target", ""),
            })

        @bus.subscribe("scan.started")
        async def on_scan_start(event):
            await self.broadcast("scan.started", {
                "target": getattr(event, "target", ""),
                "mode": getattr(event, "mode", ""),
            })

        @bus.subscribe("scan.completed")
        async def on_scan_complete(event):
            await self.broadcast("scan.completed", {
                "target": getattr(event, "target", ""),
                "total_findings": getattr(event, "total_findings", 0),
                "duration": getattr(event, "duration", 0),
            })

        self._subscribed = True


_ws_api: Optional[WebSocketAPI] = None


def get_ws_api() -> WebSocketAPI:
    global _ws_api
    if _ws_api is None:
        _ws_api = WebSocketAPI()
    return _ws_api
