"""
Phase 3 – Stats panel (Strix‑style).
Shows scan duration, agents progress, and total findings.
Will be updated by the UI (placeholder implementation for now).
"""

from textual.widgets import Static
from rich.text import Text
from rich.style import Style

class StatsPanel(Static):
    """Simple stats display.

    For now it just shows static placeholder text; later it will be updated
    live from the orchestrator/tracer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_stats(duration=0.0, agents=0, findings=0)

    def update_stats(self, duration: float, agents: int, findings: int) -> None:
        """Refresh the displayed stats.

        Args:
            duration: Scan duration in seconds.
            agents: Number of agents currently running.
            findings: Total findings discovered.
        """
        txt = Text()
        txt.append("⏱ Duration: ", style=Style(color="cyan"))
        txt.append(f"{duration:.2f}s\n", style=Style(color="white"))
        txt.append("🤖 Agents: ", style=Style(color="cyan"))
        txt.append(f"{agents}\n", style=Style(color="white"))
        txt.append("🔍 Findings: ", style=Style(color="cyan"))
        txt.append(str(findings), style=Style(color="white"))
        self.update(txt)
