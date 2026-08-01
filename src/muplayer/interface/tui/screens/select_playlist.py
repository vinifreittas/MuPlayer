"""
SelectPlaylistModal — ModalScreen for adding the active song to a playlist (DT-32).

Behaviour:
- Shows all existing playlists as a selectable list.
- Provides an input field to create a brand-new playlist on the fly.
- Dismisses with the chosen playlist name (str) or None if the user cancels.
"""

from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from muplayer.domain.playlist import Playlist
from muplayer.utils.i18n import t


class SelectPlaylistModal(ModalScreen[str | None]):
    """Modal for selecting or creating a playlist to add the current song to."""

    BINDINGS: ClassVar = [("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    SelectPlaylistModal {
        align: center middle;
    }

    #modal-container {
        width: 50;
        height: auto;
        max-height: 30;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    #modal-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #playlist-list {
        height: auto;
        max-height: 10;
        border: solid $primary-darken-1;
        margin-bottom: 1;
    }

    #new-playlist-label {
        margin-top: 1;
        color: $text-muted;
    }

    #new-playlist-input {
        margin-bottom: 1;
    }

    #modal-buttons {
        height: auto;
        align: right middle;
    }

    #confirm-btn {
        margin-right: 1;
    }
    """

    def __init__(self, playlists: list[Playlist], **kwargs) -> None:
        super().__init__(**kwargs)
        self._playlists = playlists
        self._selected_name: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static(t("modal_add_title"), id="modal-title")

            if self._playlists:
                yield Label(t("modal_existing_playlists"))
                with ListView(id="playlist-list"):
                    for playlist in self._playlists:
                        count = playlist.song_count
                        label = f"{playlist.name}  ({count} song{'s' if count != 1 else ''})"
                        yield ListItem(Label(label), id=f"pl-{playlist.name}")
            else:
                yield Label(t("modal_no_playlists"), id="no-playlists-label")

            yield Label(t("modal_create_new"), id="new-playlist-label")
            yield Input(placeholder=t("modal_new_placeholder"), id="new-playlist-input")

            with Horizontal(id="modal-buttons"):
                yield Button(t("modal_btn_add"), variant="primary", id="confirm-btn")
                yield Button(t("modal_btn_cancel"), variant="default", id="cancel-btn")

    @on(ListView.Selected, "#playlist-list")
    def _on_list_selected(self, event: ListView.Selected) -> None:
        """Highlights the clicked playlist and stores its name."""
        if event.item.id:
            # Strip the "pl-" prefix we added in compose()
            self._selected_name = event.item.id.removeprefix("pl-")

    @on(Input.Changed, "#new-playlist-input")
    def _on_input_changed(self, event: Input.Changed) -> None:
        """When typing a new name, clear the list selection."""
        if event.value.strip():
            self._selected_name = None  # new name takes priority

    @on(Button.Pressed, "#confirm-btn")
    def _on_confirm(self) -> None:
        new_name = self.query_one("#new-playlist-input", Input).value.strip()
        result = new_name if new_name else self._selected_name
        self.dismiss(result)

    @on(Button.Pressed, "#cancel-btn")
    def action_cancel(self) -> None:
        self.dismiss(None)
