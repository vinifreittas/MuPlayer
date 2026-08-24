from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Any

from textual import on, work
from textual.css.query import NoMatches
from textual.message_pump import MessagePump

from muplayer.infrastructure.i18n import t
from muplayer.interface.tui.widgets import MiniPlayer, SearchView, SongList

if TYPE_CHECKING:
    from muplayer.application.playback_service import PlaybackService
    from muplayer.infrastructure.config import ConfigManager

logger = logging.getLogger(__name__)


class PlaybackMixin(MessagePump):
    """Mixin responsible for audio playback control, progress updates, and MiniPlayer events."""

    playback_service: PlaybackService
    config_manager: ConfigManager
    is_playing: bool
    current_time: int
    is_shuffling: bool
    is_repeating: bool
    update_timer: Any

    def _play_track(self, index: int) -> None:
        """Selects track in service and triggers background worker for audio."""
        # 1. Atualiza a UI para o estado PAUSADO e zera o tempo instantaneamente
        self.is_playing = False
        self.current_time = 0

        # 2. Atualiza a fila e a faixa ativa (o service intercala a parada do player)
        song = self.playback_service.select_track(index)
        if not song:
            return

        # 3. Atualiza as informações da nova música no MiniPlayer mantendo-o pausado
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).current_song = song

        # 4. Inicia a thread de carregamento/extração em background
        self._start_audio_worker()

    @work(thread=True, exclusive=True)
    def _start_audio_worker(self) -> None:
        """Background thread worker for media loading and playback engine ignition."""
        try:
            self.playback_service.prepare_and_play_active()
            # Sucesso: apenas agora alteramos a UI para "Tocando"
            self.call_from_thread(setattr, self, "is_playing", True)
        except ValueError:
            self.call_from_thread(self.notify, t("playback_missing_url"), severity="error")
            self.call_from_thread(setattr, self, "is_playing", False)
        except Exception as e:
            logger.error(f"Playback failed: {e}")
            self.call_from_thread(self.notify, t("playback_engine_error"), severity="error")
            self.call_from_thread(setattr, self, "is_playing", False)

    # --------------------------------------------------------------------------
    # REACTIVE WATCHERS
    # --------------------------------------------------------------------------

    def watch_is_playing(self, is_playing: bool) -> None:
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).is_playing = is_playing

        if is_playing:
            self.playback_service.play()
        else:
            self.playback_service.pause()

        if self.update_timer:
            if is_playing:
                self.update_timer.resume()
            else:
                self.update_timer.pause()

    def watch_current_time(self, seconds: int) -> None:
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).time_elapsed = seconds

    def watch_is_shuffling(self, is_shuffling: bool) -> None:
        self.playback_service.is_shuffling = is_shuffling
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).is_shuffling = is_shuffling

    def watch_is_repeating(self, is_repeating: bool) -> None:
        self.playback_service.is_repeating = is_repeating
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).is_repeating = is_repeating

    # --------------------------------------------------------------------------
    # KEYBINDING ACTIONS
    # --------------------------------------------------------------------------

    def action_toggle_play(self) -> None:
        # Se a música estiver em processo de extração/carregamento, ignora a tecla
        if getattr(self.playback_service, "is_loading", False):
            return

        self.is_playing = self.playback_service.toggle_play()

    def action_volume_up(self) -> None:
        new_vol = self.playback_service.adjust_volume(+5)
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).volume = new_vol
        self.config_manager.update(volume=new_vol)

    def action_volume_down(self) -> None:
        new_vol = self.playback_service.adjust_volume(-5)
        with contextlib.suppress(NoMatches):
            self.query_one(MiniPlayer).volume = new_vol
        self.config_manager.update(volume=new_vol)

    def action_next_track(self) -> None:
        self._handle_next_track()

    def action_prev_track(self) -> None:
        self._handle_prev_track()

    def action_toggle_shuffle(self) -> None:
        self.is_shuffling = not self.is_shuffling

    def action_toggle_repeat(self) -> None:
        self.is_repeating = not self.is_repeating

    def _update_playback_progress(self) -> None:
        current_time, should_advance = self.playback_service.update_progress()
        self.current_time = current_time

        if should_advance:
            self.is_playing = False
            self._handle_next_track()

    # --------------------------------------------------------------------------
    # UI EVENT HANDLERS
    # --------------------------------------------------------------------------

    @on(MiniPlayer.TogglePlay)
    def _handle_miniplayer_toggle(self) -> None:
        self.action_toggle_play()

    @on(MiniPlayer.ToggleShuffle)
    def _handle_toggle_shuffle(self) -> None:
        self.action_toggle_shuffle()

    @on(MiniPlayer.ToggleRepeat)
    def _handle_toggle_repeat(self) -> None:
        self.action_toggle_repeat()

    @on(SearchView.SongSelected)
    @on(SongList.SongSelected)
    def _handle_song_selection(self, event: SearchView.SongSelected | SongList.SongSelected) -> None:
        idx = self.playback_service.set_queue(event.context_songs, start_song=event.song)
        self._play_track(idx)

    @on(SongList.PlayAll)
    def _handle_play_all(self, event: SongList.PlayAll) -> None:
        if event.context_songs:
            idx = self.playback_service.set_queue(event.context_songs)
            self._play_track(idx)

    @on(MiniPlayer.NextTrack)
    def _handle_next_track(self) -> None:
        next_idx = self.playback_service.get_next_index()
        if next_idx is None:
            self.is_playing = False
            return
        self._play_track(next_idx)

    @on(MiniPlayer.PrevTrack)
    def _handle_prev_track(self) -> None:
        prev_idx = self.playback_service.get_prev_index()
        self._play_track(prev_idx)
