"""
Bug Bounty Mode - specialized classes for bug bounty workflows
"""

from argus.core.logger import get_logger
from argus.core.config import get_config
from argus.agents.base_agent import Finding

logger = get_logger()

from argus.agents.bugbounty.scope_analyzer import ScopeAnalyzer
from argus.agents.bugbounty.duplicate_checker import DuplicateChecker
from argus.agents.bugbounty.report_drafter import ReportDrafter
from argus.agents.bugbounty.chain_builder import ChainBuilder
from argus.agents.bugbounty.quality_checker import QualityChecker

__all__ = [
    "ScopeAnalyzer",
    "DuplicateChecker",
    "ReportDrafter",
    "ChainBuilder",
    "QualityChecker",
    "logger",
]
