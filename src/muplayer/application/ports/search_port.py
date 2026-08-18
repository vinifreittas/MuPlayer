from abc import ABC, abstractmethod

from muplayer.domain import Song


class SearchPort(ABC):
    """Port defining the contract for media search and audio URL extraction."""

    @abstractmethod
    def search(self, query: str, max_results: int = 15) -> list[Song]:
        """Search for songs matching the query."""
        ...

    @abstractmethod
    def extract_audio_url(self, video_url: str) -> tuple[str | None, str | None]:
        """Extract a direct audio stream URL and HTTP User-Agent from a video URL."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release search-related resources."""
        ...
