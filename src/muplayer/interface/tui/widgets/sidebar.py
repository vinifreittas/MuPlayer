import contextlib

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView

from muplayer.infrastructure.i18n import t


class Sidebar(Vertical):
    """Isolated Widget responsible for side navigation and playlist listings."""

    playlist_names = reactive[list[str]]([])

    class PlaylistSelected(Message):
        def __init__(self, name: str):
            super().__init__()
            self.name = name

    def compose(self) -> ComposeResult:
        yield Label(t("sidebar_library"), id="lib-title", classes="section-title")
        with ListView(id="library-list"):
            yield ListItem(Label(t("sidebar_home")), id="item-home")
            yield ListItem(Label(t("sidebar_discover")), id="item-discover")
            yield ListItem(Label(t("sidebar_radio")), id="item-radio")

        yield Label(t("sidebar_playlists"), id="pl-title", classes="section-title")
        yield ListView(id="playlist-items")

    def update_translations(self) -> None:
        """Update static label texts to match current locale."""
        with contextlib.suppress(NoMatches):
            self.query_one("#lib-title", Label).update(t("sidebar_library"))
            self.query_one("#item-home Label", Label).update(t("sidebar_home"))
            self.query_one("#item-discover Label", Label).update(t("sidebar_discover"))
            self.query_one("#item-radio Label", Label).update(t("sidebar_radio"))
            self.query_one("#pl-title", Label).update(t("sidebar_playlists"))

    def watch_playlist_names(self, playlist_names: list[str]):
        playlist_listview = self.query_one("#playlist-items", ListView)
        playlist_listview.clear()

        for name in playlist_names:
            playlist_listview.append(ListItem(Label(name)))

    @on(ListView.Selected, "#playlist-items")
    def _on_playlist_click(self, event: ListView.Selected) -> None:
        if isinstance(event.item, ListItem):
            with contextlib.suppress(NoMatches):
                playlist_name = str(event.item.query_one(Label).renderable)
                self.post_message(self.PlaylistSelected(playlist_name))
