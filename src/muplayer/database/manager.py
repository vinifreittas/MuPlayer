import logging
from pathlib import Path
from typing import Any

from tortoise import Tortoise
from tortoise.transactions import in_transaction

from muplayer.database.tables import Playlist as PlaylistsTable
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

    def _to_pydantic_model(self, playlist_db: PlaylistsTable) -> Playlist:
        """Helper to cleanly transform a database row into a Pydantic domain model."""
        return Playlist(
            name=playlist_db.name,
            songs=[Song.model_validate(song, from_attributes=True) for song in playlist_db.songs],
        )

    async def get_playlists(self) -> list[Playlist]:
        """Retrieves all playlists along with their associated songs."""
        playlists_db = await PlaylistsTable.all().prefetch_related("songs")
        return [self._to_pydantic_model(p) for p in playlists_db]

    async def get_playlist_by_name(self, name: str) -> Playlist | None:
        """Retrieves a single playlist by its unique name."""
        playlist_db = await PlaylistsTable.filter(name=name).prefetch_related("songs").first()
        return self._to_pydantic_model(playlist_db) if playlist_db else None

    async def create_playlist(self, playlist_data: Playlist) -> Playlist | None:
        """Creates a new playlist and links its songs atomically within a transaction."""
        async with in_transaction():
            playlist_db = await PlaylistsTable.create(name=playlist_data.name)

            for song in playlist_data.songs:
                song_db, _ = await SongsTable.get_or_create(
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    duration=song.duration,
                    defaults={"source": song.source},
                )
                await playlist_db.songs.add(song_db)

        return await self.get_playlist_by_name(playlist_data.name)

    async def update_playlist(self, current_name: str, new_data: Playlist) -> Playlist | None:
        """Updates a playlist's name and syncs its song relations atomically."""
        async with in_transaction():
            playlist_db = await PlaylistsTable.filter(name=current_name).first()
            if not playlist_db:
                return None

            playlist_db.name = new_data.name
            await playlist_db.save()

            await playlist_db.songs.clear()
            for song in new_data.songs:
                song_db, _ = await SongsTable.get_or_create(
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    duration=song.duration,
                    defaults={"source": song.source},
                )
                await playlist_db.songs.add(song_db)

        return await self.get_playlist_by_name(new_data.name)

    async def delete_playlist(self, name: str) -> bool:
        """Deletes a playlist by its name."""
        playlist_db = await PlaylistsTable.filter(name=name).first()
        if not playlist_db:
            return False

        await playlist_db.delete()
        return True
