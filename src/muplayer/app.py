import contextlib
import inspect
import logging
from pathlib import Path
from typing import Any, ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from muplayer.database import DatabaseManager
from muplayer.interface.screens import Configurations
from muplayer.interface.themes import spotify_dark_theme
from muplayer.interface.widgets import Header, MiniPlayer, SearchView, Sidebar, SongList
from muplayer.models import Song
from muplayer.services import PlayerAPI, SearchAPI
from muplayer.utils import Cache, configure_logging
from muplayer.utils.config import ConfigManager

# Configuration Constants
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
configure_logging(log_dir=DATA_DIR / "logs")


class MuPlayer(App[None]):
    """A professional, thread-safe TUI Music Player using Textual."""

    TITLE = "MuPlayer"
    CSS_PATH = "interface/style.tcss"
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

    # Reactive state variables
    is_playing: reactive[bool] = reactive(False)
    current_time: reactive[int] = reactive(0)
    is_shuffling: reactive[bool] = reactive(False)
    is_repeating: reactive[bool] = reactive(False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Core Infrastructure Dependencies
        self.config_manager = ConfigManager(config_path=DATA_DIR / "config.json")
        self.cache = Cache(cache_dir=DATA_DIR / "cache")
        self.db = DatabaseManager(db_path=DATA_DIR / "app_data.db")
        self.player_api = PlayerAPI()
        self.search_api = SearchAPI(cache_client=self.cache)

        # Playback State Management
        self.active_song: Song | None = None
        self.current_queue: list[Song] = []
        self.current_queue_idx: int = -1
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

        await self.db.connect()

        # Wire initial database state to UI components safely
        if playlists := await self.db.get_playlists():
            self.query_one(Sidebar).playlist_names = [p.name for p in playlists]
            self.query_one(SongList).songs = playlists[0].songs
        else:
            self.query_one(Sidebar).playlist_names = []
            self.query_one(SongList).songs = []

        self.player_api.volume = self.config_manager.config.volume
        self.query_one(MiniPlayer).volume = self.config_manager.config.volume
        self.update_timer = self.set_interval(1.0, self._update_playback_progress, pause=True)

    async def on_unmount(self) -> None:
        """Gracefully cleans up background processes, caches, and connections."""
        logger.info("Shutting down MuPlayer safely...")

        resources_to_close = [
            ("Database", self.db.disconnect),
            ("Cache", lambda: self.cache.close() if hasattr(self.cache, "close") else None),
            ("Player API", self.player_api.close),
            ("Search API", self.search_api.close),
        ]

        for name, close_func in resources_to_close:
            try:
                if inspect.iscoroutinefunction(close_func):
                    await close_func()
                else:
                    close_func()
            except Exception as e:
                logger.error(f"Failed to close {name} cleanly: {e}")

    def _play_track(self, index: int) -> None:
        """Validates bounds and switches the active track safely."""
        if not self.current_queue or not (0 <= index < len(self.current_queue)):
            self.is_playing = False
            return

        self.current_queue_idx = index
        self.active_song = self.current_queue[index]
        self.current_time = 0

        self.query_one(MiniPlayer).current_song = self.active_song
        self._start_audio_worker(self.active_song.source)

    @work(thread=True, exclusive=True)
    def _start_audio_worker(self, url: str) -> None:
        """Handles background audio URL extraction and playback safely."""
        try:
            audio_url = self.search_api.extract_audio_url(url) or url
            if self.player_api.play(audio_url):
                self.call_from_thread(setattr, self, "is_playing", True)
        except Exception as e:
            logger.error(f"Playback failed for {url}: {e}")
            self.call_from_thread(setattr, self, "is_playing", False)

    def watch_is_playing(self, is_playing: bool) -> None:
        """Responds automatically to changes in the `is_playing` reactive state."""
        self.query_one(MiniPlayer).is_playing = is_playing

        # Drive API state based on reactive changes
        if is_playing:
            self.player_api.resume()
        else:
            self.player_api.pause()

        # Handle progress timer coordination toggle
        if self.update_timer:
            if is_playing:
                self.update_timer.resume()
            else:
                self.update_timer.pause()

    def watch_current_time(self, seconds: int) -> None:
        self.query_one(MiniPlayer).time_elapsed = seconds

    def action_toggle_play(self) -> None:
        if self.active_song:
            self.is_playing = not self.is_playing

    def action_volume_up(self) -> None:
        new_vol = min(100, self.player_api.volume + 5)
        self.player_api.volume = new_vol
        self.query_one(MiniPlayer).volume = new_vol
        self.config_manager.update(volume=new_vol)

    def action_volume_down(self) -> None:
        new_vol = max(0, self.player_api.volume - 5)
        self.player_api.volume = new_vol
        self.query_one(MiniPlayer).volume = new_vol
        self.config_manager.update(volume=new_vol)

    def action_next_track(self) -> None:
        self._handle_next_track()

    def action_prev_track(self) -> None:
        self._handle_prev_track()

    def action_toggle_shuffle(self) -> None:
        self.is_shuffling = not self.is_shuffling
        # The visual update for buttons could go to a watcher or directly here
        # But we'll handle the logic in next_track

    def action_toggle_repeat(self) -> None:
        self.is_repeating = not self.is_repeating

    def watch_is_shuffling(self, is_shuffling: bool) -> None:
        try:
            btn = self.query_one(MiniPlayer).query_one("#shuffle-btn", Button)
            if is_shuffling:
                btn.add_class("active")
            else:
                btn.remove_class("active")
        except Exception:
            pass

    def watch_is_repeating(self, is_repeating: bool) -> None:
        try:
            btn = self.query_one(MiniPlayer).query_one("#repeat-btn", Button)
            if is_repeating:
                btn.add_class("active")
            else:
                btn.remove_class("active")
        except Exception:
            pass

    def _update_playback_progress(self) -> None:
        if not self.is_playing or not self.active_song:
            return

        self.current_time += 1
        duration = getattr(self.active_song, "duration", 0)

        if self.current_time >= duration:
            self.current_time = 0
            self.is_playing = False
            self._handle_next_track()

    # --------------------------------------------------------------------------
    # EVENT HANDLERS
    # --------------------------------------------------------------------------

    @on(MiniPlayer.TogglePlay)
    def _handle_miniplayer_toggle(self) -> None:
        self.action_toggle_play()

    @on(Sidebar.PlaylistSelected)
    async def _handle_playlist_selection(self, event: Sidebar.PlaylistSelected) -> None:
        if playlist := await self.db.get_playlist_by_name(event.name):
            self.query_one(SongList).songs = playlist.songs
        else:
            self.query_one(SongList).songs = []
        self.query_one(ContentSwitcher).current = "dashboard-view"

    @on(SearchView.SongSelected)
    @on(SongList.SongSelected)
    def _handle_song_selection(self, event: Any) -> None:
        self.current_queue = event.context_songs
        try:
            idx = self.current_queue.index(event.song)
        except ValueError:
            idx = 0
        self._play_track(idx)

    @on(SongList.PlayAll)
    def _handle_play_all(self, event: SongList.PlayAll) -> None:
        if event.context_songs:
            self.current_queue = event.context_songs
            self._play_track(0)

    @on(MiniPlayer.NextTrack)
    def _handle_next_track(self) -> None:
        if not self.current_queue:
            return

        import random

        next_idx = random.randint(0, len(self.current_queue) - 1) if self.is_shuffling else self.current_queue_idx + 1

        if next_idx >= len(self.current_queue):
            if self.is_repeating:
                next_idx = 0
            else:
                self.is_playing = False
                return

        self._play_track(next_idx)

    @on(MiniPlayer.PrevTrack)
    def _handle_prev_track(self) -> None:
        # Re-play track if past 3 seconds, otherwise go to previous
        target_idx = self.current_queue_idx if self.current_time > 3 else self.current_queue_idx - 1
        self._play_track(target_idx)

    @on(Header.HomeCalled)
    def _handle_home(self, event: Any) -> None:
        self.query_one(ContentSwitcher).current = "dashboard-view"

    @on(Header.SettingsCalled)
    def _handle_settings(self, event: Any) -> None:
        def check_settings(new_settings: dict[str, Any] | None) -> None:
            if new_settings:
                self.config_manager.update(**new_settings)

        self.push_screen(Configurations(config=self.config_manager.config), check_settings)

    @on(Header.SearchSubmitted)
    def _handle_search(self, event: Header.SearchSubmitted) -> None:
        self._execute_search_worker(event.query)

    @work(thread=True, exclusive=True)
    def _execute_search_worker(self, query: str) -> None:
        """Executes API search on a background thread safely."""
        self.call_from_thread(self._set_loading, True)
        try:
            limit = self.config_manager.config.search_limit
            results = self.search_api.search(query, limit)

            self.call_from_thread(self._apply_search_results, results)
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            self.call_from_thread(self._set_loading, False)

    def _set_loading(self, is_loading: bool) -> None:
        with contextlib.suppress(Exception):
            self.query_one(SearchView).loading = is_loading

    def _apply_search_results(self, results: list[Any]) -> None:
        """Main-thread execution target to update UI elements safely."""
        self._set_loading(False)
        search_view = self.query_one(SearchView)
        search_view.search_results = results
        self.query_one(ContentSwitcher).current = "search-view"
