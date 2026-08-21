from __future__ import annotations

import logging
from typing import Literal

from muplayer.application.ports import AudioPort
from muplayer.infrastructure.audio.backends import MpvBackend, PlayerBackend, VlcBackend

logger = logging.getLogger(__name__)

# Maps engine name strings to their backend classes
_ENGINE_MAP: dict[str, type[PlayerBackend]] = {
    "mpv": MpvBackend,
    "vlc": VlcBackend,
}


class PlayerAPI(AudioPort):
    """Handles core audio playback features using a standard PlayerBackend interface."""

    def __init__(self, engine: Literal["mpv", "vlc"]) -> None:
        self._engine = engine
        self._player: PlayerBackend | None = None
        logger.debug(f"PlayerAPI wrapper instantiated with engine='{engine}' (lazy loading active).")

    @property
    def player(self) -> PlayerBackend:
        """Lazy initialization using the engine specified at construction time."""
        if self._player is None:
            self._player = self._init_backend()
        return self._player

    def _init_backend(self) -> PlayerBackend:
        """Instantiates the backend for the engine received from the caller."""
        backend_cls = _ENGINE_MAP.get(self._engine)
        if backend_cls is None:
            raise ValueError(f"Unknown audio engine: '{self._engine}'. Valid options: {list(_ENGINE_MAP)}.")
        try:
            return backend_cls()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize '{self._engine}' backend: {e}") from e

    @property
    def volume(self) -> int:
        return self.player.volume

    @volume.setter
    def volume(self, value: int) -> None:
        clamped_value = max(0, min(100, value))
        logger.debug(f"Setting volume to {clamped_value}.")
        self.player.volume = clamped_value

    @property
    def is_paused(self) -> bool:
        return self.player.is_paused

    @is_paused.setter
    def is_paused(self, value: bool) -> None:
        self.player.is_paused = value

    def play(self, source: str, user_agent: str | None = None) -> bool:
        if not source:
            logger.warning("Attempted to play an empty audio source.")
            return False

        logger.info(f"Playing source: {source}")
        try:
            self.player.play(source, user_agent=user_agent)
            self.is_paused = False
            return True
        except Exception as e:
            logger.error(f"Player error while trying to play: {e}", exc_info=True)
            return False

    def get_time(self) -> int:
        """Returns the current playback position in seconds from the audio engine (DT-33)."""
        if self._player is None:
            return 0
        return self._player.get_time()

    def pause(self) -> None:
        logger.info("Pausing player.")
        self.is_paused = True

    def resume(self) -> None:
        logger.info("Resuming player.")
        self.is_paused = False

    def toggle_pause(self) -> None:
        logger.info("Toggling player pause state.")
        self.is_paused = not self.is_paused

    def close(self) -> None:
        if self._player is not None:
            try:
                self._player.terminate()
                logger.debug("PlayerAPI backend terminated successfully.")
            except Exception as e:
                logger.warning(f"Failed to cleanly terminate player backend: {e}")
            finally:
                self._player = None
