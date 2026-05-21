"""
Toolkit — browser, proxy, shell, python runtime, and fuzzer
"""

from argus.toolkit.browser import BrowserAutomation
from argus.toolkit.http_proxy import HTTPProxy
from argus.toolkit.shell import ShellExecutor
from argus.toolkit.python_runtime import PythonRuntime

try:
    from argus.toolkit.fuzzer import FuzzerEngine, FuzzResult
except ImportError:
    FuzzerEngine = None
    FuzzResult = None

__all__ = [
    "BrowserAutomation",
    "HTTPProxy",
    "ShellExecutor",
    "PythonRuntime",
    "FuzzerEngine",
    "FuzzResult",
]
