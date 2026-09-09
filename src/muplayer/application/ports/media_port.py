from abc import ABC, abstractmethod


class MediaPort(ABC):
    """Port defining the contract for audio stream URL resolution and media extraction."""

    @abstractmethod
    def extract_audio_url(self, video_url: str) -> str | None:
        """Extract a direct audio stream URL from a video or media URL."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release media-related resources."""
        ...
