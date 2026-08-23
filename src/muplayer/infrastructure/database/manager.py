import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from tortoise import Tortoise
from tortoise.transactions import in_transaction

from muplayer.application.ports import StoragePort
from muplayer.domain import Playlist, Song
from muplayer.infrastructure.database.config import get_tortoise_config
from muplayer.infrastructure.database.tables import PlaylistSongTable, PlaylistTable, SongTable

logger = logging.getLogger(__name__)


class DatabaseManager(StoragePort):
    """Acts as a Data Access Layer (DAL) API for the application, managing Tortoise ORM operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._config = self._build_config()

    def _build_config(self) -> dict[str, Any]:
        """Dynamically generates the Tortoise ORM configuration dictionary."""
        return get_tortoise_config(self.db_path)

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

    # --------------------------------------------------------------------------
    # READ OPERATIONS
    # --------------------------------------------------------------------------

    async def get_playlists(self, limit: int = 50, offset: int = 0) -> list[Playlist]:
        """Retrieves playlists with pagination support, along with their associated songs. (DT-10)"""
        playlists_db = await PlaylistTable.all().offset(offset).limit(limit)

        # O(1) Query to avoid N+1 problem on startup
        playlist_songs = await PlaylistSongTable.all().order_by("playlist_id", "order").prefetch_related("song")

        grouped_songs: dict[int, list[Song]] = defaultdict(list)
        for ps in playlist_songs:
            song = Song.model_validate(ps.song, from_attributes=True)
            grouped_songs[ps.playlist_id].append(song.model_copy(update={"added_at": ps.added_at}))

        result = []
        for p in playlists_db:
            result.append(
                Playlist(
                    id=p.id,
                    name=p.name,
                    created_at=p.created_at,
                    songs=grouped_songs.get(p.id, []),
                )
            )
        return result

    async def get_playlist_by_name(self, name: str) -> Playlist | None:
        """Retrieves a single playlist by its unique name, with songs ordered."""
        playlist_db = await PlaylistTable.filter(name=name).first()
        if not playlist_db:
            return None

        playlist_songs = await PlaylistSongTable.filter(playlist=playlist_db).order_by("order").prefetch_related("song")
        songs = [
            Song.model_validate(ps.song, from_attributes=True).model_copy(update={"added_at": ps.added_at})
            for ps in playlist_songs
        ]

        return Playlist(id=playlist_db.id, name=playlist_db.name, created_at=playlist_db.created_at, songs=songs)

    # --------------------------------------------------------------------------
    # WRITE OPERATIONS
    # --------------------------------------------------------------------------

    async def create_playlist(self, name: str) -> Playlist | None:
        """Creates a new playlist. Returns None if a playlist with that name already exists. (DT-08)"""
        try:
            playlist_db = await PlaylistTable.create(name=name)
            logger.info(f"Playlist '{name}' created with id={playlist_db.id}.")
            return Playlist(id=playlist_db.id, name=playlist_db.name, created_at=playlist_db.created_at)
        except Exception as e:
            logger.error(f"Failed to create playlist '{name}': {e}")
            return None

    async def delete_playlist(self, name: str) -> bool:
        """Deletes a playlist and all its song associations. Returns True if successful. (DT-08)"""
        playlist_db = await PlaylistTable.filter(name=name).first()
        if not playlist_db:
            logger.warning(f"Attempted to delete non-existent playlist: '{name}'")
            return False

        # Cascade: remove all PlaylistSong entries first, then the playlist
        await PlaylistSongTable.filter(playlist=playlist_db).delete()
        await playlist_db.delete()
        logger.info(f"Playlist '{name}' and all its song entries deleted.")
        return True

    async def add_song_to_playlist(self, playlist_name: str, song: Song) -> bool:
        """Adds a song to the end of a playlist. Updates source URL if song already exists. (DT-07)"""
        async with in_transaction():
            playlist_db = await PlaylistTable.filter(name=playlist_name).first()
            if not playlist_db:
                logger.warning(f"Playlist '{playlist_name}' not found.")
                return False

            song_db, created = await SongTable.get_or_create(
                title=song.title,
                artist=song.artist,
                album=song.album,
                duration=song.duration,
                defaults={"source": song.source},
            )

            # DT-07: If song already existed but has a newer/valid URL, sync it
            if not created and song.source and song_db.source != song.source:
                song_db.source = song.source
                await song_db.save(update_fields=["source"])
                logger.debug(f"Updated source URL for song '{song.title}' (id={song_db.id}).")

            max_order_record = await PlaylistSongTable.filter(playlist=playlist_db).order_by("-order").first()
            next_order = (max_order_record.order + 1) if max_order_record else 0

            await PlaylistSongTable.create(playlist=playlist_db, song=song_db, order=next_order)
            logger.info(f"Song '{song.title}' added to playlist '{playlist_name}' at position {next_order}.")
            return True

    async def remove_song_from_playlist(self, playlist_name: str, song_index: int) -> bool:
        """Removes a song at a given order index and compacts remaining positions. (DT-08)"""
        playlist_db = await PlaylistTable.filter(name=playlist_name).first()
        if not playlist_db:
            logger.warning(f"Playlist '{playlist_name}' not found.")
            return False

        entry = await PlaylistSongTable.filter(playlist=playlist_db, order=song_index).first()
        if not entry:
            logger.warning(f"No song at index {song_index} in playlist '{playlist_name}'.")
            return False

        async with in_transaction():
            await entry.delete()
            # Compact: shift all higher-order entries down by 1
            subsequent = await PlaylistSongTable.filter(playlist=playlist_db, order__gt=song_index).order_by("order")
            for ps in subsequent:
                ps.order -= 1
                await ps.save(update_fields=["order"])

        logger.info(f"Song at index {song_index} removed from playlist '{playlist_name}'. Positions compacted.")
        return True
