from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import ListView

from muplayer.domain import Song
from muplayer.interface.tui.widgets.song_item import SongItem


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

    def watch_search_results(self, search_results: list[Song]) -> None:
        song_listview = self.query_one("#song-results", ListView)
        song_listview.clear()
        if search_results:
            items = [SongItem(idx, song) for idx, song in enumerate(search_results, start=1)]
            song_listview.mount(*items)

    @on(ListView.Selected, ".song-items")
    def _on_song_click(self, event: ListView.Selected) -> None:
        if isinstance(event.item, SongItem):
            self.post_message(self.SongSelected(event.item.song, self.search_results))
