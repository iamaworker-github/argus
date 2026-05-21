"""Textual UI exports for Argus.

Imports are intentionally lazy so lightweight cockpit modules do not pull in
scanner/browser dependencies during test collection or simple terminal startup.
"""


def run_strix_ui(*args, **kwargs):
    from argus.ui.strix_app import run_strix_ui as _run_strix_ui

    return _run_strix_ui(*args, **kwargs)


def run_argus_tui(*args, **kwargs):
    from argus.ui.argus_tui import main as _run_argus_tui

    return _run_argus_tui(*args, **kwargs)
