from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, ListItem

from muplayer.domain import Song
from muplayer.interface.tui.helpers import format_time


class SongItem(ListItem):
    """Visual wrapper for rendering individual songs inside a ListView."""

    def __init__(self, idx: int, song: Song, **kwargs):
        super().__init__(**kwargs)
        self.song_idx = idx
        self.song = song

    def on_enter(self, event: events.Enter) -> None:
        self.add_class("-hover")

    def on_leave(self, event: events.Leave) -> None:
        self.remove_class("-hover")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(str(self.song_idx), classes="song-idx")
            yield Label(self.song.title, classes="song-title")
            yield Label(self.song.artist, classes="song-artist")
            yield Label(format_time(self.song.duration), classes="song-duration")
