import logging

import diskcache

from muplayer.application.ports import AudioPort, SearchPort
from muplayer.domain import QueueState, Song

logger = logging.getLogger(__name__)


class PlaybackService:
    """Gerencia fila, engine de áudio, resolução de mídia e regras de reprodução."""

    def __init__(self, player_api: AudioPort, search_api: SearchPort, cache: diskcache.Cache | None = None) -> None:
        self.player_api = player_api
        self.search_api = search_api
        self.cache = cache
        self._queue = QueueState()
        self._is_playing: bool = False
        self._is_loading: bool = False
        self._current_time: int = 0

    # ------------------------------------------------------------------
    # Propriedades de conveniência
    # ------------------------------------------------------------------

    @property
    def active_song(self) -> Song | None:
        return self._queue.active_song

    @property
    def current_queue(self) -> list[Song]:
        return self._queue.songs

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @is_playing.setter
    def is_playing(self, value: bool) -> None:
        self._is_playing = value

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @property
    def current_time(self) -> int:
        return self._current_time

    @property
    def is_shuffling(self) -> bool:
        return self._queue.is_shuffling

    @is_shuffling.setter
    def is_shuffling(self, value: bool) -> None:
        self._queue.is_shuffling = value

    @property
    def is_repeating(self) -> bool:
        return self._queue.is_repeating

    @is_repeating.setter
    def is_repeating(self, value: bool) -> None:
        self._queue.is_repeating = value

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def set_queue(self, songs: list[Song], start_song: Song | None = None) -> int:
        """Atualiza a fila atual e retorna o índice da música selecionada."""
        return self._queue.set_songs(songs, start_song=start_song)

    def select_track(self, index: int) -> Song | None:
        """Valida e define a faixa ativa no índice especificado."""
        selected = self._queue.select_track(index)
        if selected is None:
            self.pause()
            self._is_loading = False
            return None

        self.player_api.pause()
        self._is_playing = False
        self._is_loading = True
        self._current_time = 0
        return selected

    # ------------------------------------------------------------------
    # Playback & Stream Resolution
    # ------------------------------------------------------------------

    def extract_audio_url(self, url: str) -> str | None:
        """Extrai URL direta de reprodução com gerenciamento de cache."""
        cache_key = f"yt:audio_url:{url}"

        if self.cache:
            cached_url = self.cache.get(cache_key)
            if cached_url and isinstance(cached_url, str):
                logger.debug(f"Cache hit for audio URL: '{url}'")
                return cached_url

        audio_url = self.search_api.extract_audio_url(url)

        if audio_url and self.cache:
            self.cache.set(cache_key, audio_url, expire=3600)  # 1 hora TTL

        if audio_url:
            return audio_url

        # Do not return YouTube webpage URLs as fallback, as MPV cannot play web URLs with ytdl=False
        if url.startswith(("http://", "https://")) and ("youtube.com/watch" in url or "youtu.be/" in url):
            logger.warning(f"Failed to extract direct audio URL for YouTube webpage: {url}")
            return None

        return url

    def invalidate_audio_cache(self, url: str) -> None:
        """Invalida a entrada em cache para uma URL de áudio com falha de reprodução."""
        if self.cache:
            cache_key = f"yt:audio_url:{url}"
            self.cache.delete(cache_key)
            logger.debug(f"Invalidated cached audio URL for: '{url}'")

    def prepare_and_play_active(self) -> str:
        """Extrai a URL e inicia o player. Deve ser executado em thread separada."""
        if not self._queue.active_song or not self._queue.active_song.source:
            self._is_loading = False
            raise ValueError("playback_missing_url")

        url = self._queue.active_song.source

        try:
            audio_url = self.extract_audio_url(url)
            if not audio_url:
                self.invalidate_audio_cache(url)
                self._is_playing = False
                raise RuntimeError("playback_engine_error")

            if self.player_api.play(audio_url):
                self._is_playing = True
                return audio_url
            else:
                self.invalidate_audio_cache(url)
                self._is_playing = False
                raise RuntimeError("playback_engine_error")
        finally:
            self._is_loading = False

    def play(self) -> None:
        if self._is_loading:
            return

        if self._queue.active_song:
            self.player_api.resume()
            self._is_playing = True

    def pause(self) -> None:
        self.player_api.pause()
        self._is_playing = False

    def toggle_play(self) -> bool:
        if self._is_loading:
            return self._is_playing

        if self._queue.active_song:
            if self._is_playing:
                self.pause()
            else:
                self.play()
        return self._is_playing

    # ------------------------------------------------------------------
    # Volume (fonte da verdade: player_api)
    # ------------------------------------------------------------------

    def get_volume(self) -> int:
        return self.player_api.volume

    def set_volume(self, volume: int) -> int:
        new_vol = max(0, min(100, volume))
        self.player_api.volume = new_vol
        return new_vol

    def adjust_volume(self, delta: int) -> int:
        return self.set_volume(self.player_api.volume + delta)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def get_next_index(self) -> int | None:
        """Determina o índice da próxima faixa com base nas regras de shuffle e repeat."""
        return self._queue.get_next_index()

    def get_prev_index(self) -> int:
        """Retorna o índice da faixa anterior considerando o tempo corrido."""
        return self._queue.get_prev_index(current_time=self._current_time)

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    def update_progress(self) -> tuple[int, bool]:
        """Atualiza a posição atual de reprodução."""
        if not self._is_playing or not self._queue.active_song or self.player_api.is_paused:
            return self._current_time, False

        engine_time = self.player_api.get_time()
        if engine_time > 0:
            self._current_time = engine_time
        else:
            self._current_time += 1

        duration = self._queue.active_song.duration
        if duration > 0 and self._current_time >= duration:
            self._current_time = 0
            self._is_playing = False
            return 0, True

        return self._current_time, False
