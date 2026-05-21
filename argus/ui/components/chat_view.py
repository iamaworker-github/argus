"""
ChatGPT-style Main Chat View for Argus TUI
Modern messaging interface with AI responses
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Input, RichLog, Button
from textual import on
from datetime import datetime


class MessageBubble(Static):
    def __init__(self, content: str, is_user: bool = False, timestamp: str = "", **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")

    def compose(self) -> ComposeResult:
        if self.is_user:
            yield Container(
                Static(f"[#d1d5db]{self.content}[/]", classes="user-message"),
                Static(f"[#6b7280]{self.timestamp}[/]", classes="msg-timestamp"),
                classes="user-bubble",
            )
        else:
            yield Container(
                Static("🤖", classes="ai-avatar"),
                Container(
                    Static(f"[#a78bfa]{self.content}[/]", classes="ai-message"),
                    Static(f"[#6b7280]{self.timestamp}[/]", classes="msg-timestamp"),
                    classes="ai-bubble-content",
                ),
                classes="ai-bubble",
            )


class ChatView(Container):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []

    def compose(self) -> ComposeResult:
        yield Static("CHAT VIEW", classes="empty-state")

    def add_message(self, content: str, is_user: bool = False):
        self.messages.append((content, is_user))
        self.refresh()


class WelcomePanel(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(classes="welcome-container"):
            yield Static("🔍", classes="welcome-icon")
            yield Static("ARGUS", classes="welcome-title")
            yield Static("AI-Powered Security Testing Platform", classes="welcome-subtitle")

            yield Static("", classes="welcome-spacer")

            yield Static("Quick Actions", classes="quick-actions-title")

            with Horizontal(classes="quick-actions-grid"):
                yield Button("🎯  Pentest Scan", id="quick-pentest", variant="primary")
                yield Button("💰  Bug Bounty", id="quick-bugbounty", variant="primary")
                yield Button("🏆  CTF Mode", id="quick-ctf", variant="primary")
                yield Button("🔍  OSINT Recon", id="quick-osint", variant="primary")
                yield Button("💰  Bug Bounty", id="quick-bb", variant="primary")
                yield Button("🔌  API Security", id="quick-api", variant="primary")
                yield Button("📁  Code Analysis", id="quick-code", variant="primary")


class CommandInput(Input):
    def __init__(self, **kwargs):
        super().__init__(
            placeholder="Type a command or select a scan mode...",
            id="command-input",
            **kwargs
        )

    def on_mount(self):
        self.focus()


class ArgusChatView(Container):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []
        self.current_mode = "pentest"

    def compose(self) -> ComposeResult:
        with Horizontal(classes="chat-layout"):
            with Vertical(classes="chat-main"):
                yield ScrollableContainer(id="messages-container")

                with Container(id="input-area"):
                    yield CommandInput()
                    yield Button("▶ Send", id="send-btn", variant="primary")

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content, "time": datetime.now().strftime("%H:%M")})
        self.refresh_messages()

    def add_ai_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content, "time": datetime.now().strftime("%H:%M")})
        self.refresh_messages()

    def refresh_messages(self):
        try:
            container = self.query_one("#messages-container", ScrollableContainer)
            container.remove_children()

            for msg in self.messages:
                if msg["role"] == "user":
                    container.mount(
                        Container(
                            Static(f"[#d1d5db]{msg['content']}[/]", classes="user-msg-text"),
                            Static(f"[#6b7280]{msg['time']}[/]", classes="msg-time"),
                            classes="user-msg",
                        )
                    )
                else:
                    container.mount(
                        Container(
                            Static("🤖", classes="ai-icon"),
                            Container(
                                Static(f"[#a78bfa]{msg['content']}[/]", classes="ai-msg-text"),
                                Static(f"[#6b7280]{msg['time']}[/]", classes="msg-time"),
                            ),
                            classes="ai-msg",
                        )
                    )
            container.scroll_end(animate=False)
        except Exception:
            pass

    @on(Button.Pressed, "#send-btn")
    def on_send(self):
        input_widget = self.query_one("#command-input", Input)
        if input_widget.value.strip():
            self.add_user_message(input_widget.value.strip())
            self.add_ai_message(f"Processing: {input_widget.value.strip()}")
            input_widget.value = ""

    @on(Input.Submitted, "#command-input")
    def on_submit(self, event: Input.Submitted):
        if event.value.strip():
            self.add_user_message(event.value.strip())
            self.add_ai_message(f"Processing: {event.value.strip()}")
            event.input.value = ""