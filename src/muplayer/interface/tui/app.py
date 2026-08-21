import contextlib
import logging
from typing import Any, ClassVar

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import ContentSwitcher

from muplayer.application.library_service import LibraryService
from muplayer.application.playback_service import PlaybackService
from muplayer.application.search_service import SearchService
from muplayer.infrastructure.config import ConfigManager
from muplayer.infrastructure.i18n import set_locale
from muplayer.interface.tui.controllers import NavigationMixin, PlaybackMixin, SearchMixin
from muplayer.interface.tui.themes import spotify_dark_theme
from muplayer.interface.tui.widgets import Header, MiniPlayer, SearchView, Sidebar, SongList

logger = logging.getLogger(__name__)


class MuPlayer(PlaybackMixin, SearchMixin, NavigationMixin, App[None]):
    """A professional, thread-safe TUI Music Player using Textual."""

    TITLE = "MuPlayer"
    CSS_PATH = "style.tcss"
    THEMES: ClassVar = [spotify_dark_theme]
    BINDINGS: ClassVar = [
        ("space", "toggle_play", "Play/Pause"),
        ("ctrl+up", "volume_up", "Volume +"),
        ("ctrl+down", "volume_down", "Volume -"),
        ("ctrl+right", "next_track", "Next Track"),
        ("ctrl+left", "prev_track", "Prev Track"),
        ("s", "toggle_shuffle", "Shuffle"),
        ("r", "toggle_repeat", "Repeat"),
        ("a", "add_to_playlist", "Add Song"),
    ]

    # Reactive state variables for UI bindings
    is_playing: reactive[bool] = reactive(False)
    current_time: reactive[int] = reactive(0)
    is_shuffling: reactive[bool] = reactive(False)
    is_repeating: reactive[bool] = reactive(False)

    def __init__(
        self,
        playback_service: PlaybackService,
        library_service: LibraryService,
        search_service: SearchService,
        config_manager: ConfigManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.playback_service = playback_service
        self.library_service = library_service
        self.search_service = search_service
        self.config_manager = config_manager
        self.update_timer = None

    def compose(self) -> ComposeResult:
        """Builds the primary visual structure of the application."""
        yield Header()
        with ContentSwitcher(initial="dashboard-view"):
            with Horizontal(id="dashboard-view"):
                yield Sidebar()
                yield SongList()
            yield SearchView(id="search-view")
        yield MiniPlayer()

    async def on_mount(self) -> None:
        """Handles asynchronous application initialization and resource wiring."""
        for theme in self.THEMES:
            self.register_theme(theme)
        self.theme = "spotify-dark"

        await self.library_service.connect()

        # Wire initial state to UI components
        playlists = await self.library_service.get_playlists()
        with contextlib.suppress(NoMatches):
            if playlists:
                self.query_one(Sidebar).playlist_names = [p.name for p in playlists]
                self.query_one(SongList).songs = playlists[0].songs
            else:
                self.query_one(Sidebar).playlist_names = []
                self.query_one(SongList).songs = []

        initial_vol = self.playback_service.set_volume(self.config_manager.config.volume)
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).volume = initial_vol

        set_locale(self.config_manager.config.language)
        self._refresh_ui_translations()

        timer_interval = 5.0 if self.config_manager.config.efficiency_mode else 1.0
        self.update_timer = self.set_interval(timer_interval, self._update_playback_progress, pause=True)
