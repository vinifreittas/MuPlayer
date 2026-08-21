from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from ctypes.util import find_library

logger = logging.getLogger(__name__)


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
    def play(self, source: str, user_agent: str | None = None) -> None:
        """Start playing the specified source."""
        pass

    @abstractmethod
    def get_time(self) -> int:
        """Return the current playback position in whole seconds. Returns 0 if unknown."""
        pass

    @abstractmethod
    def terminate(self) -> None:
        """Safely release and close player resources."""
        pass


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

    def play(self, source: str, user_agent: str | None = None) -> None:
        if user_agent:
            try:
                self._player["user-agent"] = user_agent
            except Exception as e:
                logger.warning(f"Failed to set User-Agent on MPV backend: {e}")
        self._player.play(source)

    def get_time(self) -> int:
        """Returns current playback position in seconds via MPV's time_pos property."""
        try:
            pos = self._player.time_pos
            return int(pos) if pos is not None else 0
        except Exception:
            return 0

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

    def play(self, source: str, user_agent: str | None = None) -> None:
        if user_agent and self._instance:
            media = self._instance.media_new(source)
            media.add_option(f":http-user-agent={user_agent}")
            self._player.set_media(media)
            self._player.play()
        else:
            self._player.set_mrl(source)
            self._player.play()

    def get_time(self) -> int:
        """Returns current playback position in seconds via VLC's get_time() (ms → s)."""
        try:
            ms = self._player.get_time()
            return max(0, ms // 1000) if ms is not None and ms >= 0 else 0
        except Exception:
            return 0

    def terminate(self) -> None:
        """DT-02: Release both the media player AND the vlc.Instance to free all native memory."""
        if self._player:
            self._player.stop()
            self._player.release()
            self._player = None
        if self._instance:
            self._instance.release()
            self._instance = None
        logger.debug("VLC backend fully released (player + instance).")
