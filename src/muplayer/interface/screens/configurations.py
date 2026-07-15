from typing import ClassVar

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Select, Static, Switch

from muplayer.utils.config import AppConfig


class Configurations(ModalScreen):
    BINDINGS: ClassVar = [("escape", "dismiss", "Close")]

    def __init__(self, config: AppConfig, **kwargs):
        super().__init__(**kwargs)
        self.app_config = config

    def compose(self) -> ComposeResult:
        with Vertical(id="container"):
            # A horizontal header container to neatly align the title and the close button
            with Horizontal(id="config-header"):
                yield Label("Application Settings", id="config-title")
                yield Static("x", id="config-close-btn")

            # 1. Search Limit
            yield Label("Max Search Results:")
            yield Input(
                value=str(self.app_config.search_limit),
                placeholder="e.g., 15",
                id="config-search-limit",
                type="integer",
            )

            # 2. Language Selection
            yield Label("Language / Idioma:")
            yield Select(
                options=[("English", "en"), ("Português", "pt")], value=self.app_config.language, id="config-language"
            )

            # 3. Efficiency Mode Toggle
            with Horizontal(classes="toggle-container"):
                yield Label("Efficiency Mode:")
                yield Switch(value=self.app_config.efficiency_mode, id="config-efficiency")

    @on(events.Click, "#config-close-btn")
    def _on_close_click(self) -> None:
        self.action_dismiss()

    def action_dismiss(self) -> None:
        # Before dismissing, gather values and return them so app.py can save
        try:
            search_limit_val = int(self.query_one("#config-search-limit", Input).value)
        except ValueError:
            search_limit_val = 15

        new_settings = {
            "search_limit": max(1, min(search_limit_val, 50)),  # clamp between 1 and 50
            "language": self.query_one("#config-language", Select).value,
            "efficiency_mode": self.query_one("#config-efficiency", Switch).value,
        }
        self.dismiss(new_settings)
