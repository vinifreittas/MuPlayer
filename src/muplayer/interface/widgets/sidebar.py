from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView


class Sidebar(Vertical):
    """Isolated Widget responsible for side navigation and playlist listings."""

    playlist_names = reactive[list[str]]([])

    class PlaylistSelected(Message):
        def __init__(self, name: str):
            super().__init__()
            self.name = name

    def compose(self) -> ComposeResult:
        yield Label("LIBRARY", classes="section-title")
        with ListView(id="library-list"):
            yield ListItem(Label("🏠 Home"))
            yield ListItem(Label("🔍 Discover"))
            yield ListItem(Label("📻 Radio"))

        yield Label("PLAYLISTS", classes="section-title")
        yield ListView(id="playlist-items")

    def watch_playlist_names(self, playlist_names: list[str]):
        playlist_listview = self.query_one("#playlist-items", ListView)
        playlist_listview.clear()

        for name in playlist_names:
            playlist_listview.append(ListItem(Label(name)))

    @on(ListView.Selected, "#playlist-items")
    def _on_playlist_click(self, event: ListView.Selected) -> None:
        if isinstance(event.item, ListItem):
            playlist_name = str(event.item.query_one(Label).content)
            self.post_message(self.PlaylistSelected(playlist_name))
