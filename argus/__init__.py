"""
Argus - AI-Powered Security Testing Platform
See Everything. Miss Nothing.
"""

__version__ = "2.0.0"
__author__ = "Argus Security Team"
__description__ = "AI-Powered Security Testing Platform"

from argus.core.config import Config
from argus.core.logger import get_logger

__all__ = ["Config", "get_logger", "__version__"]
