from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from textual import on
from textual.css.query import NoMatches
from textual.message_pump import MessagePump
from textual.widgets import ContentSwitcher

from muplayer.domain import Song
from muplayer.infrastructure.i18n import set_locale, t
from muplayer.interface.tui.screens import Configurations, SelectPlaylistModal
from muplayer.interface.tui.widgets import Header, MiniPlayer, Sidebar, SongList

if TYPE_CHECKING:
    from muplayer.application.library_service import LibraryService
    from muplayer.application.playback_service import PlaybackService
    from muplayer.infrastructure.config import ConfigManager


class NavigationMixin(MessagePump):
    """Mixin responsible for view switching, playlist management, modal screens, and i18n translation updates."""

    playback_service: PlaybackService
    library_service: LibraryService
    config_manager: ConfigManager
    active_view: str
    update_timer: Any

    def watch_active_view(self, active_view: str) -> None:
        """Single point of contact with ContentSwitcher — reacts to the active_view reactive."""
        with contextlib.suppress(NoMatches):
            self.query_one(ContentSwitcher).current = active_view

    async def action_add_to_playlist(self) -> None:
        """Opens playlist modal for the active song."""
        active_song = self.playback_service.active_song
        if not active_song:
            self.notify(t("no_active_song"), severity="warning")
            return

        playlists = await self.library_service.get_playlists()

        def handle_modal_result(selected_name: str | None) -> None:
            if selected_name:
                self.run_worker(
                    self._async_add_to_playlist(selected_name, active_song),
                    exclusive=False,
                )

        self.push_screen(SelectPlaylistModal(playlists), handle_modal_result)

    async def _async_add_to_playlist(self, playlist_name: str, song: Song) -> None:
        """Async worker delegating playlist operations to LibraryService."""
        success, msg = await self.library_service.add_song_to_playlist(playlist_name, song)
        severity = "information" if success else "error"
        self.notify(msg, severity=severity)

        if success:
            playlists = await self.library_service.get_playlists()
            with contextlib.suppress(NoMatches):
                self.query_one(Sidebar).playlist_names = [p.name for p in playlists]
            if updated := await self.library_service.get_playlist_by_name(playlist_name):
                with contextlib.suppress(NoMatches):
                    self.query_one(SongList).songs = updated.songs

    @on(Sidebar.PlaylistSelected)
    async def _handle_playlist_selection(self, event: Sidebar.PlaylistSelected) -> None:
        playlist = await self.library_service.get_playlist_by_name(event.name)
        songs = playlist.songs if playlist else []

        with contextlib.suppress(NoMatches):
            self.query_one(SongList).songs = songs
        self.active_view = "dashboard-view"

    @on(Header.HomeCalled)
    def _handle_home(self, event: Any) -> None:
        self.active_view = "dashboard-view"

    def _refresh_ui_translations(self) -> None:
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
                    self.update_timer.interval = 5.0 if new_settings["efficiency_mode"] else 1.0

        self.push_screen(Configurations(config=self.config_manager.config), check_settings)
