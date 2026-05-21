import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from argus.core.logger import get_logger
from argus.core.blackboard import FindingCategory, get_blackboard

logger = get_logger()

_active_scans: Dict[str, Dict[str, Any]] = {}


async def run_scan(target: str, mode: str = "pentest", depth: str = "deep") -> str:
    from argus.cli import _create_mode_orchestrator
    scan_id = str(uuid.uuid4())
    if mode == "auto":
        from argus.agents.modes.autonomous import AutonomousOrchestrator
        orchestrator = AutonomousOrchestrator(target, scan_depth=depth)
    else:
        orchestrator = _create_mode_orchestrator(target, mode=mode, scan_depth=depth)
    orchestrator.load_agents()
    _active_scans[scan_id] = {
        "target": target,
        "mode": mode,
        "depth": depth,
        "status": "running",
        "orchestrator": orchestrator,
        "start_time": datetime.now().isoformat(),
    }
    try:
        result = await orchestrator.run_sequential()
        _active_scans[scan_id]["status"] = "completed"
        _active_scans[scan_id]["result"] = result.to_dict()
        _active_scans[scan_id]["end_time"] = datetime.now().isoformat()
    except Exception as e:
        _active_scans[scan_id]["status"] = "failed"
        _active_scans[scan_id]["error"] = str(e)
    return scan_id


async def get_status(scan_id: str) -> Dict[str, Any]:
    scan = _active_scans.get(scan_id)
    if not scan:
        return {"error": f"Scan {scan_id} not found"}
    return {
        "scan_id": scan_id,
        "target": scan["target"],
        "mode": scan["mode"],
        "status": scan["status"],
        "start_time": scan.get("start_time"),
        "end_time": scan.get("end_time"),
    }


async def list_findings(scan_id: str) -> List[Dict[str, Any]]:
    scan = _active_scans.get(scan_id)
    if not scan:
        return []
    result = scan.get("result")
    if not result:
        return []
    return result.get("findings", [])


async def medusa_scan(target: str, git_mode: bool = False) -> Dict[str, Any]:
    from argus.toolkit.medusa_integration import MedusaIntegration
    if not MedusaIntegration.check_available():
        return {"error": "medusa-security not installed. Run: pip install medusa-security"}
    if git_mode:
        result = MedusaIntegration.scan_git_repo(target)
    else:
        result = MedusaIntegration.scan_path(target)
    if result.error:
        return {"error": result.error}
    return {
        "total_issues": result.total_issues,
        "files_scanned": result.files_scanned,
        "security_score": result.security_score,
        "risk_level": result.risk_level,
        "severity_breakdown": result.severity_breakdown,
        "findings": [
            {
                "severity": f.severity,
                "issue": f.issue,
                "file": f.file,
                "line": f.line,
                "scanner": f.scanner,
            }
            for f in result.findings if not f.is_likely_fp
        ],
    }


async def list_tools() -> List[Dict[str, str]]:
    return [
        {"name": "auto", "description": "Autonomous mode — auto-detects target type, selects agents, runs Medusa"},
        {"name": "osint", "description": "Passive reconnaissance (no exploitation)"},
        {"name": "bugbounty", "description": "Bug bounty methodology with validation gates"},
        {"name": "ctf", "description": "CTF challenge solving"},
        {"name": "pentest", "description": "Full penetration testing"},
        {"name": "medusa", "description": "Medusa AI security scanner (9600+ patterns for AI/ML, LLM, MCP)"},
    ]


async def get_attack_surface(scan_id: str) -> Dict[str, Any]:
    scan = _active_scans.get(scan_id)
    if not scan:
        return {"error": "Scan not found"}
    bb = get_blackboard()
    entries = bb.query(hot_only=True)
    return {
        "total_entries": len(entries),
        "entries": [e.to_dict() for e in entries[:50]],
    }
