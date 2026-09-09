from abc import ABC, abstractmethod

from muplayer.domain import Song


class SearchPort(ABC):
    """Port defining the contract for catalog search."""

    @abstractmethod
    def search(self, query: str, limit: int = 15) -> list[Song]:
        """Search for songs matching the query."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release search-related resources."""
        ...
