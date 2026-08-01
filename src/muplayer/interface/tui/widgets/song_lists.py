import contextlib

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Label, ListItem, ListView

from muplayer.domain import Song
from muplayer.interface.helpers import format_time
from muplayer.utils.i18n import t


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


class SearchView(Vertical):
    """Isolated Widget responsible for listing the tracks of the search results."""

    search_results = reactive[list[Song]]([])

    class SongSelected(Message):
        def __init__(self, song: Song, context_songs: list[Song]):
            super().__init__()
            self.song = song
            self.context_songs = context_songs

    def compose(self) -> ComposeResult:
        yield ListView(id="song-results", classes="song-items")

    def watch_search_results(self, search_results: list[Song]):
        song_listview = self.query_one("#song-results", ListView)
        song_listview.clear()

        for idx, song in enumerate(search_results, start=1):
            song_listview.append(SongItem(idx, song))

    @on(ListView.Selected, ".song-items")
    def _on_song_click(self, event: ListView.Selected) -> None:
        if isinstance(event.item, SongItem):
            self.post_message(self.SongSelected(event.item.song, self.search_results))


class SongList(Vertical):
    """Isolated Widget responsible for listing the tracks of the selected playlist."""

    songs = reactive[list[Song]]([])

    class SongSelected(Message):
        def __init__(self, song: Song, context_songs: list[Song]):
            super().__init__()
            self.song = song
            self.context_songs = context_songs

    class PlayAll(Message):
        def __init__(self, context_songs: list[Song]):
            super().__init__()
            self.context_songs = context_songs

    def compose(self) -> ComposeResult:
        with Horizontal(id="content-header"):
            yield Label(t("songs_title"), id="songs-header-title", classes="view-title")
            yield Button(t("play_all_btn"), variant="primary", id="play-all-btn")

        yield ListView(id="song-playlist", classes="song-items")

    def update_translations(self) -> None:
        """Update static label texts to match current locale."""
        with contextlib.suppress(NoMatches):
            self.query_one("#songs-header-title", Label).update(t("songs_title"))
            self.query_one("#play-all-btn", Button).label = t("play_all_btn")

    def watch_songs(self, songs: list[Song]) -> None:
        song_listview = self.query_one("#song-playlist", ListView)
        song_listview.clear()

        for idx, song in enumerate(songs, start=1):
            song_listview.append(SongItem(idx, song))

    @on(ListView.Selected, ".song-items")
    def _on_song_click(self, event: ListView.Selected) -> None:
        if isinstance(event.item, SongItem):
            self.post_message(self.SongSelected(event.item.song, self.songs))

    @on(Button.Pressed, "#play-all-btn")
    def _on_play_all_press(self) -> None:
        if self.songs:
            self.post_message(self.PlayAll(self.songs))
