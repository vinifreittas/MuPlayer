import contextlib
import inspect
import logging
from typing import Any, ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher

from muplayer.database import DatabaseManager
from muplayer.interface.screens import Configurations, SelectPlaylistModal
from muplayer.interface.themes import spotify_dark_theme
from muplayer.interface.widgets import Header, MiniPlayer, SearchView, Sidebar, SongList
from muplayer.models import Song
from muplayer.services import PlayerAPI, SearchAPI
from muplayer.utils import Cache, configure_logging, set_locale, t
from muplayer.utils.config import ConfigManager
from muplayer.utils.paths import get_cache_dir, get_data_dir, get_log_dir

logger = logging.getLogger(__name__)


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

    def __init__(self, player_engine: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Resolve platform-appropriate directories (independent of CWD)
        data_dir = get_data_dir()
        configure_logging(log_dir=get_log_dir())

        # Core Infrastructure Dependencies
        self.config_manager = ConfigManager(config_path=data_dir / "config.json")
        set_locale(self.config_manager.config.language)
        self.cache = Cache(cache_dir=get_cache_dir())
        self.db = DatabaseManager(db_path=data_dir / "app_data.db")
        self.player_api = PlayerAPI(engine=player_engine)
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
            with contextlib.suppress(NoMatches):
                self.query_one(Sidebar).playlist_names = [p.name for p in playlists]
                self.query_one(SongList).songs = playlists[0].songs
        else:
            with contextlib.suppress(NoMatches):
                self.query_one(Sidebar).playlist_names = []
                self.query_one(SongList).songs = []

        self.player_api.volume = self.config_manager.config.volume
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).volume = self.config_manager.config.volume

        # DT-25: Activate the configured locale and refresh all mounted widget texts
        set_locale(self.config_manager.config.language)
        self._refresh_ui_translations()

        # DT-26: Efficiency mode — poll every 5s instead of 1s to reduce CPU usage
        timer_interval = 5.0 if self.config_manager.config.efficiency_mode else 1.0
        self.update_timer = self.set_interval(timer_interval, self._update_playback_progress, pause=True)

    async def on_unmount(self) -> None:
        """Gracefully cleans up background processes, caches, and connections."""
        logger.info("Shutting down MuPlayer safely...")

        resources_to_close = [
            ("Database", self.db.disconnect),
            ("Cache", self.cache.close),  # DT-24: Cache always has .close(), no hasattr needed
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

        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).current_song = self.active_song
        self._start_audio_worker(self.active_song.source)

    @work(thread=True, exclusive=True)
    def _start_audio_worker(self, url: str | None) -> None:
        """Handles background audio URL extraction and playback safely."""
        # DT-04: Explicit guard — never attempt playback without a source URL
        if not url:
            self.call_from_thread(self.notify, t("playback_missing_url"), severity="error")
            self.call_from_thread(setattr, self, "is_playing", False)
            return

        try:
            audio_url = self.search_api.extract_audio_url(url) or url
            if self.player_api.play(audio_url):
                self.call_from_thread(setattr, self, "is_playing", True)
            else:
                self.search_api.invalidate_audio_url_cache(url)
                self.call_from_thread(self.notify, t("playback_engine_error"), severity="error")
                self.call_from_thread(setattr, self, "is_playing", False)
        except Exception as e:
            logger.error(f"Playback failed for {url}: {e}")
            self.search_api.invalidate_audio_url_cache(url)
            self.call_from_thread(setattr, self, "is_playing", False)

    def watch_is_playing(self, is_playing: bool) -> None:
        """Responds automatically to changes in the `is_playing` reactive state."""
        with contextlib.suppress(NoMatches):
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
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).time_elapsed = seconds

    def action_toggle_play(self) -> None:
        if self.active_song:
            self.is_playing = not self.is_playing

    def action_volume_up(self) -> None:
        new_vol = min(100, self.player_api.volume + 5)
        self.player_api.volume = new_vol
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).volume = new_vol
        self.config_manager.update(volume=new_vol)

    def action_volume_down(self) -> None:
        new_vol = max(0, self.player_api.volume - 5)
        self.player_api.volume = new_vol
        with contextlib.suppress(NoMatches):
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

    async def action_add_to_playlist(self) -> None:
        """DT-32: Opens the playlist selection modal for the active song."""
        if not self.active_song:
            self.notify(t("no_active_song"), severity="warning")
            return

        playlists = await self.db.get_playlists()

        def handle_modal_result(selected_name: str | None) -> None:
            if not selected_name:
                return
            # Run the async DB operation safely from the callback context
            self.run_worker(
                self._async_add_to_playlist(selected_name, self.active_song),
                exclusive=False,
            )

        self.push_screen(SelectPlaylistModal(playlists), handle_modal_result)

    async def _async_add_to_playlist(self, playlist_name: str, song: Song | None) -> None:
        """Async worker: adds song to existing playlist, or creates it first."""
        if not song:
            return
        # Create playlist if it doesn't exist yet
        existing = await self.db.get_playlist_by_name(playlist_name)
        if not existing:
            created = await self.db.create_playlist(playlist_name)
            if not created:
                self.notify(f"Falha ao criar playlist '{playlist_name}'.", severity="error")
                return
            # Refresh sidebar
            playlists = await self.db.get_playlists()
            with contextlib.suppress(NoMatches):
                self.query_one(Sidebar).playlist_names = [p.name for p in playlists]

        success = await self.db.add_song_to_playlist(playlist_name, song)
        if success:
            self.notify(t("song_added_to_playlist", title=song.title, playlist=playlist_name), severity="information")
            # Refresh Sidebar list and active playlist view automatically
            playlists = await self.db.get_playlists()
            with contextlib.suppress(NoMatches):
                self.query_one(Sidebar).playlist_names = [p.name for p in playlists]
            if updated := await self.db.get_playlist_by_name(playlist_name):
                with contextlib.suppress(NoMatches):
                    self.query_one(SongList).songs = updated.songs
        else:
            self.notify(t("song_add_failed", playlist=playlist_name), severity="error")

    def watch_is_shuffling(self, is_shuffling: bool) -> None:
        """DT-12: Use suppress(NoMatches) instead of bare except to avoid masking real errors."""
        with contextlib.suppress(NoMatches):
            btn = self.query_one(MiniPlayer).query_one("#shuffle-btn", Button)
            btn.set_class(is_shuffling, "active")

    def watch_is_repeating(self, is_repeating: bool) -> None:
        """DT-12: Use suppress(NoMatches) instead of bare except to avoid masking real errors."""
        with contextlib.suppress(NoMatches):
            btn = self.query_one(MiniPlayer).query_one("#repeat-btn", Button)
            btn.set_class(is_repeating, "active")

    def _update_playback_progress(self) -> None:
        if not self.is_playing or not self.active_song:
            return

        # DT-33: Prefer real engine time; fall back to timer increment if engine not ready yet
        engine_time = self.player_api.get_time()
        if engine_time > 0:
            self.current_time = engine_time
        else:
            self.current_time += 1

        duration = getattr(self.active_song, "duration", 0)

        if duration > 0 and self.current_time >= duration:
            self.current_time = 0
            self.is_playing = False
            self._handle_next_track()

    # --------------------------------------------------------------------------
    # EVENT HANDLERS
    # --------------------------------------------------------------------------

    @on(MiniPlayer.TogglePlay)
    def _handle_miniplayer_toggle(self) -> None:
        self.action_toggle_play()

    @on(MiniPlayer.ToggleShuffle)
    def _handle_toggle_shuffle(self) -> None:
        """DT-11: Handles ToggleShuffle message from MiniPlayer widget."""
        self.action_toggle_shuffle()

    @on(MiniPlayer.ToggleRepeat)
    def _handle_toggle_repeat(self) -> None:
        """DT-11: Handles ToggleRepeat message from MiniPlayer widget."""
        self.action_toggle_repeat()

    @on(Sidebar.PlaylistSelected)
    async def _handle_playlist_selection(self, event: Sidebar.PlaylistSelected) -> None:
        if playlist := await self.db.get_playlist_by_name(event.name):
            with contextlib.suppress(NoMatches):
                self.query_one(SongList).songs = playlist.songs
        else:
            with contextlib.suppress(NoMatches):
                self.query_one(SongList).songs = []
        with contextlib.suppress(NoMatches):
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

        if self.is_shuffling and len(self.current_queue) > 1:
            # DT-34: Exclude the currently playing track from the random pool
            import random

            available = [i for i in range(len(self.current_queue)) if i != self.current_queue_idx]
            next_idx = random.choice(available)
        else:
            next_idx = self.current_queue_idx + 1

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
        with contextlib.suppress(NoMatches):
            self.query_one(ContentSwitcher).current = "dashboard-view"

    def _refresh_ui_translations(self) -> None:
        """Propagate locale updates to all mounted widgets live (DT-25)."""
        for widget_cls in (Header, Sidebar, SongList, MiniPlayer):
            with contextlib.suppress(NoMatches):
                w = self.query_one(widget_cls)
                if hasattr(w, "update_translations"):
                    w.update_translations()

    @on(Header.SettingsCalled)
    def _handle_settings(self, event: Any) -> None:
        def check_settings(new_settings: dict[str, Any] | None) -> None:
            if new_settings:
                self.config_manager.update(**new_settings)
                if lang := new_settings.get("language"):
                    set_locale(lang)
                    self._refresh_ui_translations()
                if "efficiency_mode" in new_settings and self.update_timer:
                    timer_interval = 5.0 if new_settings["efficiency_mode"] else 1.0
                    self.update_timer.interval = timer_interval

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
            self.call_from_thread(self._apply_search_results, query, results)
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            self.call_from_thread(self._set_loading, False)
            self.call_from_thread(self.notify, t("search_network_error", query=query), severity="error")

    def _set_loading(self, is_loading: bool) -> None:
        with contextlib.suppress(Exception):
            self.query_one(SearchView).loading = is_loading

    def _apply_search_results(self, query: str, results: list[Any]) -> None:
        """Main-thread execution target to update UI elements safely. (DT-15)"""
        self._set_loading(False)
        with contextlib.suppress(NoMatches):
            search_view = self.query_one(SearchView)
            search_view.search_results = results
            self.query_one(ContentSwitcher).current = "search-view"

        # DT-15: Notify user when search returns no results
        if not results:
            self.notify(t("search_no_results", query=query), severity="warning")
