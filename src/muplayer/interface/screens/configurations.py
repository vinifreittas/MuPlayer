from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Select, Static, Switch


class Configurations(ModalScreen):
    BINDINGS: ClassVar = [("escape", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="container"):
            # A horizontal header container to neatly align the title and the close button
            with Horizontal(id="config-header"):
                yield Label("Application Settings", id="config-title")
                yield Static("x", id="config-close-btn")

            # 1. SQLite Database File Selection
            yield Label("SQLite Database File Path:")
            yield Input(placeholder="e.g., path/to/database.db", id="config-db-path")

            # 2. Language Selection
            yield Label("Language / Idioma:")
            yield Select(options=[("English", "en"), ("Português", "pt")], value="en", id="config-language")

            # 3. Efficiency Mode Toggle
            with Horizontal(classes="toggle-container"):
                yield Label("Efficiency Mode:")
                yield Switch(value=False, id="config-efficiency")

    def on_click(self, event) -> None:
        """Closes the screen when the 'X' widget is clicked."""
        if event.widget.id == "config-close-btn":
            self.dismiss()
