from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from ctypes.util import find_library
from types import TracebackType
from typing import Literal

logger = logging.getLogger(__name__)

# =====================================================================
# BACKEND ADAPTER TEMPLATE
# =====================================================================


class PlayerBackend(ABC):
    """Abstract blueprint enforcing the structure for all audio backends."""

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if the required third-party player are installed and available."""
        pass

    @property
    @abstractmethod
    def volume(self) -> int:
        """Get the current volume level."""
        pass

    @volume.setter
    @abstractmethod
    def volume(self, value: int) -> None:
        """Set the volume level."""
        pass

    @property
    @abstractmethod
    def is_paused(self) -> bool:
        """Check if the player is paused."""
        pass

    @is_paused.setter
    @abstractmethod
    def is_paused(self, value: bool) -> None:
        """Set the pause state."""
        pass

    @abstractmethod
    def play(self, source: str) -> None:
        """Start playing the specified source."""
        pass

    @abstractmethod
    def terminate(self) -> None:
        """Safely release and close player resources."""
        pass


# =====================================================================
# BACKEND ADAPTERS
# =====================================================================


class MpvBackend(PlayerBackend):
    """Adapter for the python-mpv backend."""

    @classmethod
    def is_available(cls) -> bool:
        return find_library("mpv") is not None

    def __init__(self) -> None:
        import mpv

        self._player = mpv.MPV(video=False, ytdl=False)
        logger.debug("MPV backend initialized (ytdl=False for better RAM usage.)")

    @property
    def volume(self) -> int:
        return int(self._player.volume or 0)

    @volume.setter
    def volume(self, value: int) -> None:
        self._player.volume = value

    @property
    def is_paused(self) -> bool:
        return bool(self._player.pause)

    @is_paused.setter
    def is_paused(self, value: bool) -> None:
        self._player.pause = value

    def play(self, source: str) -> None:
        self._player.play(source)

    def terminate(self) -> None:
        self._player.terminate()


class VlcBackend(PlayerBackend):
    """Adapter for the python-vlc backend."""

    @classmethod
    def is_available(cls) -> bool:
        return find_library("vlc") is not None

    def __init__(self) -> None:
        import vlc

        self._instance = vlc.Instance("--no-video --quiet")
        self._player = self._instance.media_player_new()
        logger.debug("VLC backend initialized.")

    @property
    def volume(self) -> int:
        return max(0, self._player.audio_get_volume())

    @volume.setter
    def volume(self, value: int) -> None:
        self._player.audio_set_volume(value)

    @property
    def is_paused(self) -> bool:
        import vlc

        return self._player.get_state() == vlc.State.Paused

    @is_paused.setter
    def is_paused(self, value: bool) -> None:
        self._player.set_pause(1 if value else 0)

    def play(self, source: str) -> None:
        self._player.set_mrl(source)
        self._player.play()

    def terminate(self) -> None:
        self._player.stop()
        self._player.release()


# =====================================================================
# PUBLIC WRAPPER
# =====================================================================


# Maps engine name strings to their backend classes
_ENGINE_MAP: dict[str, type[PlayerBackend]] = {
    "mpv": MpvBackend,
    "vlc": VlcBackend,
}


class PlayerAPI:
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

    def play(self, source: str) -> bool:
        if not source:
            logger.warning("Attempted to play an empty audio source.")
            return False

        logger.info(f"Playing source: {source}")
        try:
            self.player.play(source)
            self.is_paused = False
            return True
        except Exception as e:
            logger.error(f"Player error while trying to play: {e}", exc_info=True)
            return False

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

    def __enter__(self) -> PlayerAPI:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        self.close()
