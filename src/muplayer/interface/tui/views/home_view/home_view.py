import contextlib
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.widgets import Label

from muplayer.infrastructure.i18n import t


class HomeView(Vertical):
    """Isolated Widget displaying the welcome screen when no content is active."""

    DEFAULT_CSS = (Path(__file__).parent / "home_view.tcss").read_text(encoding="utf-8")

    def compose(self) -> ComposeResult:
        yield Label(t("home_welcome_title"), id="home-title", classes="home-title")
        yield Label(t("home_welcome_subtitle"), id="home-subtitle", classes="home-subtitle")

    def update_translations(self) -> None:
        """Update static label texts to match current locale."""
        with contextlib.suppress(NoMatches):
            self.query_one("#home-title", Label).update(t("home_welcome_title"))
            self.query_one("#home-subtitle", Label).update(t("home_welcome_subtitle"))
            self.query_one("#home-hint", Label).update(t("home_welcome_hint"))
