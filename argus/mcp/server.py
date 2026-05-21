import asyncio
from typing import Any, Dict, Optional

from argus.core.logger import get_logger
from argus.mcp.tools import run_scan, get_status, list_findings, list_tools, get_attack_surface, medusa_scan
from argus.mcp.transports import handle_stdio, handle_sse

logger = get_logger()


class MCPApp:
    def __init__(self):
        self._send_callback = None

    def set_send_callback(self, callback):
        self._send_callback = callback

    async def process_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        method = msg.get("method", "")
        params = msg.get("params", {})
        msg_id = msg.get("id")

        try:
            if method == "run_scan":
                result = await run_scan(
                    target=params["target"],
                    mode=params.get("mode", "auto"),
                    depth=params.get("depth", "deep"),
                )
                return {"id": msg_id, "result": result}
            elif method == "get_status":
                result = await get_status(scan_id=params["scan_id"])
                return {"id": msg_id, "result": result}
            elif method == "list_findings":
                result = await list_findings(scan_id=params["scan_id"])
                return {"id": msg_id, "result": result}
            elif method == "list_tools":
                result = await list_tools()
                return {"id": msg_id, "result": result}
            elif method == "get_attack_surface":
                result = await get_attack_surface(scan_id=params["scan_id"])
                return {"id": msg_id, "result": result}
            elif method == "medusa_scan":
                result = await medusa_scan(
                    target=params["target"],
                    git_mode=params.get("git_mode", False),
                )
                return {"id": msg_id, "result": result}
            elif method == "ping":
                return {"id": msg_id, "result": "pong"}
            else:
                return {"id": msg_id, "error": f"Unknown method: {method}"}
        except KeyError as e:
            return {"id": msg_id, "error": f"Missing parameter: {e}"}
        except Exception as e:
            return {"id": msg_id, "error": str(e)}


def create_mcp_server() -> MCPApp:
    return MCPApp()


async def run_mcp_server(transport: str = "stdio", port: int = 8000) -> None:
    app = create_mcp_server()
    logger.info(f"Starting MCP server ({transport} transport)")

    if transport == "stdio":
        await handle_stdio(app)
    elif transport == "sse":
        await handle_sse(app, port=port)
    else:
        raise ValueError(f"Unknown transport: {transport}")
