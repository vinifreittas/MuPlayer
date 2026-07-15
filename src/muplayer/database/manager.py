import logging
from pathlib import Path
from typing import Any

from tortoise import Tortoise
from tortoise.transactions import in_transaction

from muplayer.database.tables import Playlist as PlaylistsTable
from muplayer.database.tables import PlaylistSong as PlaylistSongTable
from muplayer.database.tables import Song as SongsTable
from muplayer.models import Playlist, Song

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Acts as a Data Access Layer (DAL) API for the application, managing Tortoise ORM operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._config = self._build_config()

    def _build_config(self) -> dict[str, Any]:
        """Dynamically generates the Tortoise ORM configuration dictionary."""
        return {
            "connections": {"default": f"sqlite://{self.db_path.resolve()}"},
            "apps": {
                "models": {
                    "models": ["muplayer.database.tables"],
                    "default_connection": "default",
                }
            },
        }

    async def connect(self) -> None:
        """Initializes Tortoise ORM and safely generates database schemas."""
        try:
            await Tortoise.init(config=self._config)
            await Tortoise.generate_schemas(safe=True)
            logger.info("💾 Database connection via Tortoise ORM established.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    async def disconnect(self) -> None:
        """Safely closes all open database connections."""
        await Tortoise.close_connections()
        logger.info("💾 Database connections closed.")

    async def __aenter__(self) -> "DatabaseManager":
        """Enables async context manager usage: 'async with DatabaseManager(...) as db:'"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Ensures connections close cleanly when exiting the context manager."""
        await self.disconnect()

    async def get_playlists(self) -> list[Playlist]:
        """Retrieves all playlists along with their associated songs in the correct order."""
        playlists_db = await PlaylistsTable.all()

        # O(1) Query to avoid N+1 problem on startup
        playlist_songs = await PlaylistSongTable.all().order_by("playlist_id", "order").prefetch_related("song")

        from collections import defaultdict

        grouped_songs = defaultdict(list)
        for ps in playlist_songs:
            grouped_songs[ps.playlist_id].append(Song.model_validate(ps.song, from_attributes=True))

        result = []
        for p in playlists_db:
            result.append(Playlist(name=p.name, songs=grouped_songs.get(p.id, [])))
        return result

    async def get_playlist_by_name(self, name: str) -> Playlist | None:
        """Retrieves a single playlist by its unique name, with songs ordered."""
        playlist_db = await PlaylistsTable.filter(name=name).first()
        if not playlist_db:
            return None

        playlist_songs = await PlaylistSongTable.filter(playlist=playlist_db).order_by("order").prefetch_related("song")
        songs = [Song.model_validate(ps.song, from_attributes=True) for ps in playlist_songs]

        return Playlist(name=playlist_db.name, songs=songs)

    async def add_song_to_playlist(self, playlist_name: str, song: Song) -> bool:
        """Adds a single song to the end of a playlist."""
        async with in_transaction():
            playlist_db = await PlaylistsTable.filter(name=playlist_name).first()
            if not playlist_db:
                return False

            song_db, _ = await SongsTable.get_or_create(
                title=song.title,
                artist=song.artist,
                album=song.album,
                duration=song.duration,
                defaults={"source": song.source},
            )

            max_order_record = await PlaylistSongTable.filter(playlist=playlist_db).order_by("-order").first()
            next_order = (max_order_record.order + 1) if max_order_record else 0

            await PlaylistSongTable.create(playlist=playlist_db, song=song_db, order=next_order)
            return True
