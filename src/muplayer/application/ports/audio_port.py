from abc import ABC, abstractmethod


class AudioPort(ABC):
    """Port defining the contract for audio playback engines."""

    @abstractmethod
    def play(self, source: str, user_agent: str | None = None) -> bool:
        """Start playing from the given audio source URL, optionally specifying User-Agent."""
        ...

    @abstractmethod
    def pause(self) -> None:
        """Pause the current playback."""
        ...

    @abstractmethod
    def resume(self) -> None:
        """Resume paused playback."""
        ...

    @abstractmethod
    def get_time(self) -> int:
        """Return current playback position in seconds."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release all audio engine resources."""
        ...

    @property
    @abstractmethod
    def volume(self) -> int:
        """Get the current volume level (0-100)."""
        ...

    @volume.setter
    @abstractmethod
    def volume(self, value: int) -> None:
        """Set the volume level (0-100)."""
        ...
