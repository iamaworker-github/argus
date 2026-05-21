from typing import Any, Optional
from textual.widgets import Static
from rich.text import Text
from rich.style import Style
from rich.console import Group
from rich.panel import Panel


class SplashScreen(Static):
    PRIMARY_GREEN = "#22c55e"
    BANNER = (
        " █████╗ ██████╗  ██████╗ ██╗   ██╗███████╗\n"
        "██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝\n"
        "███████║██████╔╝██║  ███╗██║   ██║███████╗\n"
        "██╔══██║██╔══██╗██║   ██║██║   ██║╚════██║\n"
        "██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║\n"
        "╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝"
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._animation_step = 0
        self._animation_timer = None
        self._panel_static: Optional[Static] = None
        self._version_text = ""
        self._set_version()

    def _set_version(self) -> None:
        try:
            from argus import __version__
            self._version_text = f"v{__version__}"
        except ImportError:
            self._version_text = ""

    def compose(self) -> list:
        self._animation_step = 0
        start_line = self._build_start_line_text(0)
        panel = self._build_panel(start_line)
        panel_static = Static(panel, id="splash_content")
        self._panel_static = panel_static
        return [panel_static]

    def on_mount(self) -> None:
        self._animation_timer = self.set_interval(0.05, self._animate_start_line)

    def on_unmount(self) -> None:
        if self._animation_timer is not None:
            self._animation_timer.stop()
            self._animation_timer = None

    def _animate_start_line(self) -> None:
        if not self._panel_static:
            return
        self._animation_step += 1
        start_line = self._build_start_line_text(self._animation_step)
        panel = self._build_panel(start_line)
        self._panel_static.update(panel)

    def _build_panel(self, start_line: Text) -> Panel:
        from rich.align import Align
        content = Group(
            Align.center(Text(self.BANNER.strip("\n"), style=self.PRIMARY_GREEN, justify="center")),
            Align.center(Text(" ")),
            Align.center(self._build_welcome_text()),
            Align.center(self._build_version_text()),
            Align.center(self._build_tagline_text()),
            Align.center(Text(" ")),
            Align.center(start_line.copy()),
        )
        return Panel.fit(content, border_style=self.PRIMARY_GREEN, padding=(1, 6))

    def _build_welcome_text(self) -> Text:
        text = Text("Welcome to ", style=Style(color="white", bold=True))
        text.append("Argus", style=Style(color=self.PRIMARY_GREEN, bold=True))
        text.append("!", style=Style(color="white", bold=True))
        return text

    def _build_version_text(self) -> Text:
        return Text(self._version_text, style=Style(color="white", dim=True))

    def _build_tagline_text(self) -> Text:
        return Text("See Everything. Miss Nothing", style=Style(color="white", dim=True))

    def _build_start_line_text(self, phase: int) -> Text:
        full_text = "Starting Argus Security Scanner"
        text_len = len(full_text)
        shine_pos = phase % (text_len + 8)
        line = Text()
        for i, char in enumerate(full_text):
            dist = abs(i - shine_pos)
            if dist <= 1:
                line.append(char, style=Style(color="bright_white", bold=True))
            elif dist <= 3:
                line.append(char, style=Style(color="white", bold=True))
            elif dist <= 5:
                line.append(char, style=Style(color="#a3a3a3"))
            else:
                line.append(char, style=Style(color="#525252"))
        return line
