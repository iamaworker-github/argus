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
        from argus.agents.xxe_agent import XXEAgent
        from argus.agents.ssti_agent import SSTIAgent
        from argus.agents.open_redirect_agent import OpenRedirectAgent
        from argus.agents.cors_agent import CORSAgent
        from argus.agents.clickjacking_agent import ClickjackingAgent
        from argus.agents.nosql_injection_agent import NoSQLInjectionAgent
        from argus.agents.host_header_injection_agent import HostHeaderInjectionAgent
        from argus.agents.jwt_attack_agent import JWTTAttackAgent
        from argus.agents.rate_limit_agent import RateLimitAgent
        from argus.agents.autonomous_agent import AutonomousSecurityAgent
        from argus.agents.strix_pentest_agent import StrixPentestAgent
        from argus.agents.poc_validator_agent import PoCValidatorAgent
        _classes.update({
            "BaseAgent": BaseAgent, "Finding": Finding, "AgentResult": AgentResult, "AgentStatus": AgentStatus,
            "AgentOrchestrator": AgentOrchestrator, "ScanResult": ScanResult,
            "SQLInjectionAgent": SQLInjectionAgent, "XSSAgent": XSSAgent, "SSRFAgent": SSRFAgent,
            "ReconAgent": ReconAgent, "CommandInjectionAgent": CommandInjectionAgent,
            "AuthenticationAgent": AuthenticationAgent, "IDORAgent": IDORAgent,
            "XXEAgent": XXEAgent, "SSTIAgent": SSTIAgent,
            "OpenRedirectAgent": OpenRedirectAgent, "CORSAgent": CORSAgent,
            "ClickjackingAgent": ClickjackingAgent, "NoSQLInjectionAgent": NoSQLInjectionAgent,
            "HostHeaderInjectionAgent": HostHeaderInjectionAgent, "JWTTAttackAgent": JWTTAttackAgent,
            "RateLimitAgent": RateLimitAgent,
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
    "XXEAgent", "SSTIAgent", "OpenRedirectAgent", "CORSAgent",
    "ClickjackingAgent", "NoSQLInjectionAgent", "HostHeaderInjectionAgent",
    "JWTTAttackAgent", "RateLimitAgent",
    "AutonomousSecurityAgent", "StrixPentestAgent", "PoCValidatorAgent",
    "get_default_agents",
]
