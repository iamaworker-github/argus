"""
Phase 3 – Vulnerabilities panel (Strix‑style).
Displays a scrollable list of discovered findings with severity‑colored dots.
Each entry is clickable and will open a placeholder detail view (future work).
"""

from textual.containers import VerticalScroll
from textual.widgets import Static
from rich.text import Text
from rich.style import Style

SEVERITY_COLORS = {
    "critical": "#dc2626",  # Red
    "high": "#ea580c",      # Orange
    "medium": "#d97706",   # Amber
    "low": "#22c55e",      # Green
    "info": "#3b82f6",     # Blue
}

class VulnerabilitiesPanel(VerticalScroll):
    """Scrollable list of findings.

    The panel expects a list of dicts where each dict contains at least
    ``title`` and ``severity`` keys.  Example:

    ``[{"title": "SQL Injection", "severity": "high"}, ...]``
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._vulns: list[dict] = []

    def update_vulnerabilities(self, vulns: list[dict]):
        """Replace the current list with *vulns* and re‑render.

        ``vulns`` is a list of dictionaries containing ``title`` and ``severity``.
        """
        self._vulns = list(vulns)
        self._render()

    def _render(self) -> None:
        # Clear existing children
        for child in list(self.children):
            child.remove()

        if not self._vulns:
            self.mount(Static("No vulnerabilities found", style="dim"))
            return

        for v in self._vulns:
            title = v.get("title", "Untitled")
            severity = v.get("severity", "info").lower()
            color = SEVERITY_COLORS.get(severity, "#3b82f6")
            txt = Text()
            txt.append("● ", style=Style(color=color))
            txt.append(title, style=Style(color="#d4d4d4"))
            self.mount(Static(txt))
