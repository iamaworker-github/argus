"""
ChatGPT-style Sidebar Component for Argus TUI
Modern dark theme with clean navigation
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button, Input, RichLog
from textual import on


class SidebarItem(Static):
    def __init__(self, icon: str, label: str, active: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.label = label
        self.active = active

    def compose(self):
        bg = "#202123" if self.active else "transparent"
        color = "#ec4899" if self.active else "#d1d5db"
        yield Button(
            f"{self.icon}  {self.label}",
            id=f"nav-{self.label.lower().replace(' ', '-')}",
            variant="default",
            classes="sidebar-btn",
        )

    def on_mount(self):
        btn = self.query_one("Button")
        if self.active:
            btn.styles.background = "#202123"
            btn.styles.color = "#ec4899"


class ChatHistoryItem(Static):
    def __init__(self, title: str, timestamp: str = "", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.timestamp = timestamp

    def compose(self):
        yield Button(
            f"  {self.title}",
            id=f"chat-{hash(self.title)}",
            variant="default",
            classes="chat-item",
        )

    def on_button_pressed(self, event):
        self.app.action_load_chat(self.title)


class ArgusSidebar(ScrollableContainer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []

    def compose(self):
        yield Static("ARGUS", classes="sidebar-logo")
        yield Static("", classes="sidebar-divider")

        yield Static("  SCAN MODES", classes="sidebar-section-title")
        yield SidebarItem("🎯", "Pentest", id="nav-pentest")
        yield SidebarItem("💰", "Bug Bounty", id="nav-bugbounty")
        yield SidebarItem("🏆", "CTF", id="nav-ctf")
        yield SidebarItem("🔍", "OSINT", id="nav-osint")
        yield SidebarItem("🔌", "API Pentest", id="nav-api")

        yield Static("", classes="sidebar-divider")

        yield Static("  RECENT SCANS", classes="sidebar-section-title")
        for title in self.chat_history[-10:]:
            yield ChatHistoryItem(title)

        yield Static("", classes="sidebar-spacer")

        yield Button("  + New Scan", id="new-scan", variant="primary", classes="new-scan-btn")

        yield Static("", classes="sidebar-divider")
        yield SidebarItem("⚙️", "Settings", id="nav-settings")
        yield SidebarItem("❓", "Help", id="nav-help")

    def add_chat(self, title: str):
        self.chat_history.append(title)
        self.refresh()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "new-scan":
            self.app.action_new_scan()
        elif event.button.id and event.button.id.startswith("nav-"):
            nav_id = event.button.id.replace("nav-", "")
            self.app.action_navigate(nav_id)