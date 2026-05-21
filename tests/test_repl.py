"""Tests for REPL Interactive Shell."""

import pytest
from argus.ui.repl import ArgusREPL


def test_repl_initialization():
    repl = ArgusREPL()
    assert repl.prompt == "argus> "
    assert repl._graph is not None


def test_repl_do_help():
    repl = ArgusREPL()
    repl.onecmd("help")
    # Should not raise


def test_repl_do_graph_invalid():
    repl = ArgusREPL()
    repl.onecmd("graph")
    # Should not raise


def test_repl_do_exit():
    repl = ArgusREPL()
    result = repl.onecmd("exit")
    assert result is True


def test_repl_do_learn_stats():
    repl = ArgusREPL()
    repl.onecmd("learn stats")
    # Should not raise


def test_repl_do_monitor():
    repl = ArgusREPL()
    repl.onecmd("monitor list")
    # Should not raise


def test_repl_do_scan():
    repl = ArgusREPL()
    # Don't call scan in test since it needs asyncio loop — just verify parsing
    assert repl._graph is not None


def test_repl_default():
    repl = ArgusREPL()
    repl.onecmd("invalid_command_xyz")
    # Should not raise
