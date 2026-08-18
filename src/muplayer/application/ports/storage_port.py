from abc import ABC, abstractmethod

from muplayer.domain import Playlist, Song


class StoragePort(ABC):
    """Port defining the contract for persistent playlist/song storage."""

    @abstractmethod
    async def connect(self) -> None:
        """Initialize the storage connection."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the storage connection."""
        ...

    @abstractmethod
    async def get_playlists(self, limit: int = 50, offset: int = 0) -> list[Playlist]:
        """Retrieve playlists with pagination."""
        ...

    @abstractmethod
    async def get_playlist_by_name(self, name: str) -> Playlist | None:
        """Retrieve a single playlist by its unique name."""
        ...

    @abstractmethod
    async def create_playlist(self, name: str) -> Playlist | None:
        """Create a new playlist. Returns None if it already exists."""
        ...

    @abstractmethod
    async def delete_playlist(self, name: str) -> bool:
        """Delete a playlist and its song associations."""
        ...

    @abstractmethod
    async def add_song_to_playlist(self, playlist_name: str, song: Song) -> bool:
        """Add a song to the end of a playlist."""
        ...

    @abstractmethod
    async def remove_song_from_playlist(self, playlist_name: str, song_index: int) -> bool:
        """Remove a song at a given index and compact remaining positions."""
        ...
