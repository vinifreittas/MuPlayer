import contextlib
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.widgets import Label

from muplayer.infrastructure.i18n import t


class DiscoverView(Vertical):
    """Isolated Widget displaying the 'coming soon' placeholder for the Discover section."""

    DEFAULT_CSS = (Path(__file__).parent / "discover_view.tcss").read_text(encoding="utf-8")

    def compose(self) -> ComposeResult:
        yield Label(t("coming_soon"), id="discover-subtitle", classes="home-subtitle")

    def update_translations(self) -> None:
        """Update static label texts to match current locale."""
        with contextlib.suppress(NoMatches):
            self.query_one("#discover-subtitle", Label).update(t("coming_soon"))
