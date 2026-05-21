"""
Autonomous mode — auto-detects target type and selects optimal agents.
Just give it a target, Argus decides the rest.
"""

import re
from pathlib import Path
from typing import Optional, List

from argus.agents.modes.base import ModeOrchestrator
from argus.agents.recon_agent import ReconAgent
from argus.agents.sql_injection_agent import SQLInjectionAgent
from argus.agents.xss_agent import XSSAgent
from argus.agents.ssrf_agent import SSRFAgent
from argus.agents.command_injection_agent import CommandInjectionAgent
from argus.agents.authentication_agent import AuthenticationAgent
from argus.agents.idor_agent import IDORAgent
from argus.agents.medusa_agent import MedusaAgent
from argus.agents.strix_pentest_agent import StrixPentestAgent
from argus.agents.poc_validator_agent import PoCValidatorAgent
from argus.agents.remediation_agent import RemediationAgent
from argus.core.event_bus import EventBus
from argus.core.logger import get_logger
from argus.core import MEMORY_SYSTEM_AVAILABLE
if MEMORY_SYSTEM_AVAILABLE:
    from argus.core.memory_manager import MemoryManager

logger = get_logger()

TARGET_TYPES = {
    "url": r"^https?://",
    "domain": r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$",
    "ip": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    "directory": r"^[/~.]",
    "git_repo": r"github\.com|gitlab\.com|bitbucket\.org",
}


def detect_target_type(target: str) -> str:
    if re.match(TARGET_TYPES["url"], target):
        return "url"
    if re.match(TARGET_TYPES["git_repo"], target):
        return "git_repo"
    if re.match(TARGET_TYPES["ip"], target):
        return "ip"
    if re.match(TARGET_TYPES["directory"], target) or Path(target).exists():
        return "directory"
    if re.match(TARGET_TYPES["domain"], target):
        return "domain"
    return "unknown"


class AutonomousOrchestrator(ModeOrchestrator):
    mode_name = "autonomous"

    def __init__(
        self,
        target: str,
        event_bus: Optional[EventBus] = None,
        memory_manager: Optional['MemoryManager'] = None,
        scope: Optional[List[str]] = None,
        scan_depth: str = "deep",
        instruction: Optional[str] = None,
    ):
        super().__init__(target, event_bus, memory_manager, scope, scan_depth=scan_depth, instruction=instruction)
        self.target_type = detect_target_type(target)
        logger.info(f"🎯 Auto-detected target type: {self.target_type}")

    def load_agents(self) -> None:
        t = self.target_type
        depth = self.scan_depth

        if t == "directory":
            self._load_directory_agents()
        elif t == "git_repo":
            self._load_git_agents()
        elif t in ("url", "domain", "ip", "unknown"):
            self._load_network_agents()

    def _load_directory_agents(self) -> None:
        logger.info("📁 Directory target — running code analysis + SAST agents")
        self.add_agent(ReconAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager, mode="pentest"))
        self.add_agent(MedusaAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(StrixPentestAgent(
            self.target, event_bus=self.event_bus, memory_manager=self.memory_manager,
            scope=self.scope, scan_depth=self.scan_depth, scan_mode="pentest",
            instruction=self.instruction,
        ))
        self.add_agent(PoCValidatorAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(RemediationAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))

    def _load_git_agents(self) -> None:
        logger.info("📦 Git repo — running Medusa supply chain scan + code analysis")
        self.add_agent(MedusaAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager, scan_mode="git"))
        self.add_agent(ReconAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager, mode="pentest"))
        self.add_agent(StrixPentestAgent(
            self.target, event_bus=self.event_bus, memory_manager=self.memory_manager,
            scope=self.scope, scan_depth=self.scan_depth, scan_mode="pentest",
            instruction=self.instruction,
        ))
        self.add_agent(PoCValidatorAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(RemediationAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))

    def _load_network_agents(self) -> None:
        logger.info("🌐 Network target — running full web + API testing suite")
        self.add_agent(ReconAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager, mode="bugbounty"))
        self.add_agent(SQLInjectionAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(XSSAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(SSRFAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(CommandInjectionAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(AuthenticationAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(IDORAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(MedusaAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(StrixPentestAgent(
            self.target, event_bus=self.event_bus, memory_manager=self.memory_manager,
            scope=self.scope, scan_depth=self.scan_depth, scan_mode="pentest",
            instruction=self.instruction,
        ))
        self.add_agent(PoCValidatorAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))
        self.add_agent(RemediationAgent(self.target, event_bus=self.event_bus, memory_manager=self.memory_manager))

    def get_report_template(self) -> str:
        return "autonomous_report"

    def get_output_subdir(self) -> str:
        return f"autonomous/{self.target_type}"
