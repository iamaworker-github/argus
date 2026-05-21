"""Tests for core __init__.py lazy loading and __all__ exports."""

import argus.core


def test_core_all_exports():
    expected = [
        "RateLimiter", "TokenBucket", "get_rate_limiter",
        "PluginLoader", "get_plugin_loader",
        "AuthSessionManager", "AuthSession",
        "FuzzerEngine", "FuzzResult",
        "VulnDB", "CVELookup", "get_vulndb",
        "Notifier", "get_notifier",
        "WebSocketAPI", "get_ws_api",
        "AnomalyDetector", "get_anomaly_detector",
    ]
    for name in expected:
        assert hasattr(argus.core, name), f"Missing export: {name}"


def test_core_original_exports_still_work():
    assert hasattr(argus.core, "Config")
    assert hasattr(argus.core, "get_config")
    assert hasattr(argus.core, "EventBus")
    assert hasattr(argus.core, "get_event_bus")
    assert hasattr(argus.core, "Blackboard")
    assert hasattr(argus.core, "SessionManager")
    assert hasattr(argus.core, "SessionTracker")


def test_lazy_loading_no_circular_imports():
    # This should not raise any ImportError or circular import issues
    from argus.core.rate_limiter import RateLimiter
    from argus.core.plugin_loader import PluginLoader
    from argus.core.auth_session import AuthSessionManager
    from argus.core.vulndb import VulnDB
    from argus.core.notifier import Notifier
    from argus.core.ws_api import WebSocketAPI
    from argus.core.anomaly_detector import AnomalyDetector
    from argus.toolkit.fuzzer import FuzzerEngine
    from argus.core.distributed import RedisEventBackend
    assert RateLimiter is not None
    assert PluginLoader is not None
    assert AuthSessionManager is not None
    assert VulnDB is not None
    assert Notifier is not None
    assert WebSocketAPI is not None
    assert AnomalyDetector is not None
    assert FuzzerEngine is not None
    assert RedisEventBackend is not None
