"""Textual UI exports for Argus."""


def run_strix_ui(*args, **kwargs):
    from argus.ui.strix_app import run_strix_ui as _run_strix_ui
    return _run_strix_ui(*args, **kwargs)
