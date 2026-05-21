"""
AI-powered security testing agents

Uses lazy loading to avoid circular imports and heavy dependencies
like Playwright being loaded at import time.
"""

_loaded = False
_classes = {}

def _ensure_loaded():
    global _loaded, _classes
    if not _loaded:
        from argus.agents.base_agent import BaseAgent, Finding, AgentResult, AgentStatus
        from argus.agents.orchestrator import AgentOrchestrator, ScanResult
        from argus.agents.sql_injection_agent import SQLInjectionAgent
        from argus.agents.xss_agent import XSSAgent
        from argus.agents.ssrf_agent import SSRFAgent
        from argus.agents.recon_agent import ReconAgent
        from argus.agents.command_injection_agent import CommandInjectionAgent
        from argus.agents.authentication_agent import AuthenticationAgent
        from argus.agents.idor_agent import IDORAgent
        from argus.agents.autonomous_agent import AutonomousSecurityAgent
        from argus.agents.strix_pentest_agent import StrixPentestAgent
        from argus.agents.poc_validator_agent import PoCValidatorAgent
        _classes.update({
            "BaseAgent": BaseAgent, "Finding": Finding, "AgentResult": AgentResult, "AgentStatus": AgentStatus,
            "AgentOrchestrator": AgentOrchestrator, "ScanResult": ScanResult,
            "SQLInjectionAgent": SQLInjectionAgent, "XSSAgent": XSSAgent, "SSRFAgent": SSRFAgent,
            "ReconAgent": ReconAgent, "CommandInjectionAgent": CommandInjectionAgent,
            "AuthenticationAgent": AuthenticationAgent, "IDORAgent": IDORAgent,
            "AutonomousSecurityAgent": AutonomousSecurityAgent,
            "StrixPentestAgent": StrixPentestAgent, "PoCValidatorAgent": PoCValidatorAgent,
        })
        _loaded = True

def get_default_agents():
    _ensure_loaded()
    return [
        _classes["ReconAgent"](),
        _classes["AuthenticationAgent"](),
        _classes["CommandInjectionAgent"](),
        _classes["SQLInjectionAgent"](),
        _classes["XSSAgent"](),
        _classes["SSRFAgent"](),
        _classes["IDORAgent"](),
    ]

def __getattr__(name):
    _ensure_loaded()
    if name in _classes:
        return _classes[name]
    raise AttributeError(f"module 'argus.agents' has no attribute '{name}'")

__all__ = [
    "BaseAgent", "Finding", "AgentResult", "AgentStatus",
    "AgentOrchestrator", "ScanResult",
    "SQLInjectionAgent", "XSSAgent", "SSRFAgent", "ReconAgent",
    "CommandInjectionAgent", "AuthenticationAgent", "IDORAgent",
    "AutonomousSecurityAgent", "StrixPentestAgent", "PoCValidatorAgent",
    "get_default_agents",
]
