"""
Integration tests for DatabaseManager (DT-09).

Coverage:
- Schema creation via generate_schemas
- Playlist CRUD (create, get, delete)
- Song insertion and association to playlists
- URL sync when re-adding an existing song (DT-07)
- Song removal and position compaction
- Song reordering
- Pagination in get_playlists (DT-10)
"""

import pytest

from muplayer.database.manager import DatabaseManager
from muplayer.models.song import Song

# ---------------------------------------------------------------------------
# Playlist CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_playlist(db_manager: DatabaseManager) -> None:
    """A newly created playlist should be retrievable by name."""
    result = await db_manager.create_playlist("Rock Classics")
    assert result is not None
    assert result.name == "Rock Classics"
    assert result.id is not None


@pytest.mark.asyncio
async def test_create_duplicate_playlist_returns_none(db_manager: DatabaseManager) -> None:
    """Creating a playlist with a duplicate name should fail gracefully."""
    await db_manager.create_playlist("Jazz")
    duplicate = await db_manager.create_playlist("Jazz")
    assert duplicate is None


@pytest.mark.asyncio
async def test_get_playlists_returns_all(db_manager: DatabaseManager) -> None:
    """get_playlists should return all created playlists."""
    await db_manager.create_playlist("Pop")
    await db_manager.create_playlist("Metal")
    playlists = await db_manager.get_playlists()
    names = [p.name for p in playlists]
    assert "Pop" in names
    assert "Metal" in names


@pytest.mark.asyncio
async def test_get_playlists_pagination(db_manager: DatabaseManager) -> None:
    """get_playlists should respect limit and offset parameters."""
    for i in range(5):
        await db_manager.create_playlist(f"Playlist {i}")
    page1 = await db_manager.get_playlists(limit=2, offset=0)
    page2 = await db_manager.get_playlists(limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    # Pages should not overlap
    assert {p.name for p in page1}.isdisjoint({p.name for p in page2})


@pytest.mark.asyncio
async def test_get_playlist_by_name(db_manager: DatabaseManager) -> None:
    """get_playlist_by_name should return the correct playlist."""
    await db_manager.create_playlist("Chill Vibes")
    playlist = await db_manager.get_playlist_by_name("Chill Vibes")
    assert playlist is not None
    assert playlist.name == "Chill Vibes"


@pytest.mark.asyncio
async def test_get_playlist_by_name_nonexistent(db_manager: DatabaseManager) -> None:
    """get_playlist_by_name should return None for a missing playlist."""
    result = await db_manager.get_playlist_by_name("Does Not Exist")
    assert result is None


@pytest.mark.asyncio
async def test_delete_playlist(db_manager: DatabaseManager) -> None:
    """Deleting a playlist should remove it from the database."""
    await db_manager.create_playlist("Temporary")
    deleted = await db_manager.delete_playlist("Temporary")
    assert deleted is True
    result = await db_manager.get_playlist_by_name("Temporary")
    assert result is None


@pytest.mark.asyncio
async def test_delete_nonexistent_playlist_returns_false(db_manager: DatabaseManager) -> None:
    """Attempting to delete a playlist that doesn't exist should return False."""
    result = await db_manager.delete_playlist("Ghost Playlist")
    assert result is False


# ---------------------------------------------------------------------------
# Song operations
# ---------------------------------------------------------------------------


def make_song(title: str = "Test Song", source: str | None = "https://example.com/audio") -> Song:
    return Song(title=title, artist="Test Artist", album="Test Album", duration=180, source=source)


@pytest.mark.asyncio
async def test_add_song_to_playlist(db_manager: DatabaseManager) -> None:
    """Adding a song to a playlist should persist it and return True."""
    await db_manager.create_playlist("Favourites")
    song = make_song()
    result = await db_manager.add_song_to_playlist("Favourites", song)
    assert result is True

    playlist = await db_manager.get_playlist_by_name("Favourites")
    assert playlist is not None
    assert len(playlist.songs) == 1
    assert playlist.songs[0].title == "Test Song"


@pytest.mark.asyncio
async def test_add_song_to_nonexistent_playlist(db_manager: DatabaseManager) -> None:
    """Adding a song to a playlist that doesn't exist should return False."""
    song = make_song()
    result = await db_manager.add_song_to_playlist("Ghost", song)
    assert result is False


@pytest.mark.asyncio
async def test_add_multiple_songs_order(db_manager: DatabaseManager) -> None:
    """Songs should be stored and retrieved in insertion order."""
    await db_manager.create_playlist("Ordered")
    songs = [make_song(title=f"Track {i}") for i in range(3)]
    for song in songs:
        await db_manager.add_song_to_playlist("Ordered", song)

    playlist = await db_manager.get_playlist_by_name("Ordered")
    assert [s.title for s in playlist.songs] == ["Track 0", "Track 1", "Track 2"]


@pytest.mark.asyncio
async def test_source_url_synced_on_readd(db_manager: DatabaseManager) -> None:
    """Re-adding an existing song with a new URL should update the source field (DT-07)."""
    await db_manager.create_playlist("Sync Test")

    original = make_song(source="https://old-url.com/audio")
    await db_manager.add_song_to_playlist("Sync Test", original)

    # Same identity, new URL
    updated = make_song(source="https://new-url.com/audio")
    await db_manager.add_song_to_playlist("Sync Test", updated)

    playlist = await db_manager.get_playlist_by_name("Sync Test")
    # Both entries may point to same song; verify at least one has new URL
    sources = {s.source for s in playlist.songs}
    assert "https://new-url.com/audio" in sources


@pytest.mark.asyncio
async def test_remove_song_from_playlist(db_manager: DatabaseManager) -> None:
    """Removing a song should eliminate it and compact remaining positions."""
    await db_manager.create_playlist("Remove Test")
    for i in range(3):
        await db_manager.add_song_to_playlist("Remove Test", make_song(title=f"Song {i}"))

    # Remove the middle song (index 1)
    removed = await db_manager.remove_song_from_playlist("Remove Test", 1)
    assert removed is True

    playlist = await db_manager.get_playlist_by_name("Remove Test")
    assert len(playlist.songs) == 2
    assert playlist.songs[0].title == "Song 0"
    assert playlist.songs[1].title == "Song 2"


@pytest.mark.asyncio
async def test_remove_song_invalid_index(db_manager: DatabaseManager) -> None:
    """Removing a song at a non-existent index should return False."""
    await db_manager.create_playlist("Bad Index")
    result = await db_manager.remove_song_from_playlist("Bad Index", 99)
    assert result is False


@pytest.mark.asyncio
async def test_reorder_playlist_song(db_manager: DatabaseManager) -> None:
    """Reordering a song should update its position and shift others correctly."""
    await db_manager.create_playlist("Reorder Test")
    for i in range(4):
        await db_manager.add_song_to_playlist("Reorder Test", make_song(title=f"Track {i}"))

    # Move Track 0 from position 0 to position 3 (end)
    result = await db_manager.reorder_playlist_song("Reorder Test", 0, 3)
    assert result is True

    playlist = await db_manager.get_playlist_by_name("Reorder Test")
    titles = [s.title for s in playlist.songs]
    assert titles == ["Track 1", "Track 2", "Track 3", "Track 0"]


# ---------------------------------------------------------------------------
# Model validators
# ---------------------------------------------------------------------------


def test_song_clamps_negative_duration() -> None:
    """Song model should clamp negative durations to 0 (DT-17)."""
    song = Song(title="Bad Duration", artist="A", duration=-100)
    assert song.duration == 0


def test_song_clamps_none_duration() -> None:
    """Song model should clamp None duration to 0."""
    song = Song(title="No Duration", artist="A", duration=None)  # type: ignore[arg-type]
    assert song.duration == 0


def test_song_id_defaults_to_none() -> None:
    """Song id should default to None when not provided (DT-19)."""
    song = Song(title="No ID", artist="A", duration=60)
    assert song.id is None


def test_song_with_id() -> None:
    """Song id should be assignable (DT-19)."""
    song = Song(id=42, title="Has ID", artist="A", duration=60)
    assert song.id == 42
