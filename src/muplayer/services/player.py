from __future__ import annotations

import logging
import shutil
from abc import ABC, abstractmethod
from types import TracebackType
from typing import ClassVar

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
        return shutil.which("mpv") is not None

    def __init__(self) -> None:
        if not self.is_available():
            raise ImportError("mpv library is not installed.")
        import mpv

        self._player = mpv.MPV(video=False, ytdl=True)
        logger.debug("MPV backend initialized.")

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
        return shutil.which("vlc") is not None

    def __init__(self) -> None:
        if not self.is_available():
            raise ImportError("python-vlc library is not installed.")
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


class PlayerAPI:
    """Handles core audio playback features using a standard PlayerBackend interface."""

    # Priority registry order for backends
    _BACKEND_REGISTRY: ClassVar[list[type[PlayerBackend]]] = [MpvBackend, VlcBackend]

    def __init__(self) -> None:
        self._player: PlayerBackend | None = None
        logger.debug("PlayerAPI wrapper instantiated (lazy loading active).")

    @property
    def player(self) -> PlayerBackend:
        """Lazy initialization with automatic backend selection."""
        if self._player is None:
            self._player = self._init_backend()
        return self._player

    def _init_backend(self) -> PlayerBackend:
        """Dynamically discovers and loads the first available backend from registry."""
        for backend_cls in self._BACKEND_REGISTRY:
            if backend_cls.is_available():
                try:
                    return backend_cls()
                except Exception as e:
                    logger.warning(f"{backend_cls.__name__} was available but failed to initialize: {e}")

        raise RuntimeError("Neither MPV nor VLC media backends are available or working.")

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
