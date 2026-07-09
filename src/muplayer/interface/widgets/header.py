from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Input, Label


class Header(Horizontal):
    """Isolated Widget responsible for the top navigation bar."""

    class HomeCalled(Message):
        pass

    class SearchSubmitted(Message):
        def __init__(self, query: str):
            super().__init__()
            self.query = query

    class SettingsCalled(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Label("🎵 MuPlayer", id="title")
        yield Input(placeholder="🔍 Search for songs, artists, podcasts...", id="search-box")
        yield Label("⚙️ Settings", id="settings-btn")

    @on(events.Click, "#title")
    def _on_title_click(self) -> None:
        self.post_message(self.HomeCalled())

    @on(Input.Submitted, "#search-box")
    def _on_search_submit(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if query:
            self.post_message(self.SearchSubmitted(query))

    @on(events.Click, "#settings-btn")
    def _on_settings_click(self) -> None:
        self.post_message(self.SettingsCalled())
