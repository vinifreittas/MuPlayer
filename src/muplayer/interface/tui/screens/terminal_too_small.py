import contextlib
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label


class TerminalTooSmallScreen(ModalScreen[None]):
    """Modal screen displayed when the terminal window is smaller than minimum required dimensions."""

    BINDINGS: ClassVar = []

    def __init__(
        self,
        current_width: int,
        current_height: int,
        min_width: int,
        min_height: int,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.current_width = current_width
        self.current_height = current_height
        self.min_width = min_width
        self.min_height = min_height

    def compose(self) -> ComposeResult:
        with Vertical(id="small-term-box"):
            yield Label("⚠️  Terminal Too Small ", id="small-term-title")
            yield Label(f"Current size: {self.current_width}x{self.current_height}", id="small-term-current")
            yield Label(f"Minimum required: {self.min_width}x{self.min_height}", id="small-term-required")
            yield Label("\nPlease enlarge your terminal window.", id="small-term-hint")

    def update_dimensions(self, width: int, height: int) -> None:
        self.current_width = width
        self.current_height = height
        with contextlib.suppress(Exception):
            self.query_one("#small-term-current", Label).update(f"Current size: {width}x{height}")
