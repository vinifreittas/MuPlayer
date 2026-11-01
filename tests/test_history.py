import asyncio

import pytest

from muplayer.domain import Song
from muplayer.infrastructure.database.manager import TortoiseStorageAdapter
from muplayer.infrastructure.database.tables import HistoryTable


@pytest.fixture
async def storage_adapter(tmp_path):
    db_file = tmp_path / "test_history.db"
    adapter = TortoiseStorageAdapter(db_file)
    await adapter.connect()
    yield adapter
    await adapter.disconnect()


async def test_add_to_history_basic(storage_adapter):
    song1 = Song(title="Song 1", artist="Artist 1", source="https://youtube.com/watch?v=1")
    await storage_adapter.add_to_history(song1)

    history = await storage_adapter.get_history()
    assert len(history) == 1
    assert history[0].title == "Song 1"
    assert history[0].artist == "Artist 1"
    assert history[0].source == "https://youtube.com/watch?v=1"


async def test_add_to_history_appends_log_and_get_history_deduplicates(storage_adapter):
    """Ensures replaying a song creates new log records and get_history deduplicates by the latest occurrence."""
    source_link = "https://youtube.com/watch?v=track_one"
    song1 = Song(title="Track One", artist="Artist One", album="Album A", duration=180, source=source_link)
    await storage_adapter.add_to_history(song1)

    entry_initial = await HistoryTable.filter(source=source_link).first()
    assert entry_initial is not None
    initial_id = entry_initial.id
    initial_timestamp = entry_initial.played_at

    # Play another song in between.
    song2 = Song(
        title="Track Two",
        artist="Artist Two",
        album="Album B",
        duration=210,
        source="https://youtube.com/watch?v=track_two",
    )
    await storage_adapter.add_to_history(song2)

    # Brief pause to ensure the timestamp advances.
    await asyncio.sleep(0.01)

    # Play song 1 again with an updated title.
    song1_updated = Song(
        title="Track One (Remaster)", artist="Artist One", album="Album A", duration=185, source=source_link
    )
    await storage_adapter.add_to_history(song1_updated)

    # The database must contain 3 records (cumulative execution log).
    assert await HistoryTable.all().count() == 3

    # The 2 track_one occurrences must exist as separate rows.
    track_one_entries = await HistoryTable.filter(source=source_link).order_by("played_at")
    assert len(track_one_entries) == 2
    assert track_one_entries[0].id == initial_id
    assert track_one_entries[1].id != initial_id
    assert track_one_entries[1].played_at > initial_timestamp
    assert track_one_entries[1].title == "Track One (Remaster)"

    # The smart history query should return song1 first (most recent) and deduplicated.
    history = await storage_adapter.get_history()
    assert len(history) == 2
    assert history[0].source == source_link
    assert history[0].title == "Track One (Remaster)"
    assert history[0].duration == 185
    assert history[1].source == "https://youtube.com/watch?v=track_two"
    assert history[1].duration == 210


async def test_verification_only_by_source(storage_adapter):
    """Verifies that deduplication occurs exclusively by source."""
    # 1. Identical titles and artists with different URLs (sources) must produce 2 distinct records.
    song_v1 = Song(title="Bohemian Rhapsody", artist="Queen", source="https://youtube.com/watch?v=link_studio")
    song_v2 = Song(title="Bohemian Rhapsody", artist="Queen", source="https://youtube.com/watch?v=link_live")
    await storage_adapter.add_to_history(song_v1)
    await storage_adapter.add_to_history(song_v2)

    history = await storage_adapter.get_history()
    assert len(history) == 2
    assert {h.source for h in history} == {
        "https://youtube.com/watch?v=link_studio",
        "https://youtube.com/watch?v=link_live",
    }

    # 2. Different titles and artists with the same URL (source) produce 3 log rows and 2 deduplicated results.
    song_renamed = Song(
        title="Queen - Bohemian Rhapsody (Official)",
        artist="Queen Band",
        source="https://youtube.com/watch?v=link_live",
    )
    await storage_adapter.add_to_history(song_renamed)

    assert await HistoryTable.all().count() == 3

    history = await storage_adapter.get_history()
    assert len(history) == 2
    assert history[0].source == "https://youtube.com/watch?v=link_live"
    assert history[0].title == "Queen - Bohemian Rhapsody (Official)"


async def test_add_to_history_allows_duplicate_sources_and_preserves_metadata(storage_adapter):
    """Ensures the UNIQUE constraint was removed and complete metadata is preserved."""
    s1 = Song(title="Song 1", artist="Artist", album="Album Deluxe", duration=320, source="https://yt.com/dup")
    s2 = Song(title="Song 1 (Again)", artist="Artist", album="Album Deluxe", duration=320, source="https://yt.com/dup")

    await storage_adapter.add_to_history(s1)
    await storage_adapter.add_to_history(s2)

    assert await HistoryTable.all().count() == 2

    history = await storage_adapter.get_history()
    assert len(history) == 1
    assert history[0].title == "Song 1 (Again)"
    assert history[0].album == "Album Deluxe"
    assert history[0].duration == 320
    assert history[0].played_at is not None


async def test_get_history_limit(storage_adapter):
    """Ensures the limit parameter and newest-to-oldest ordering are respected."""
    for i in range(10):
        song = Song(title=f"Song {i}", artist="Artist", source=f"https://yt.com/{i}")
        await storage_adapter.add_to_history(song)

    history = await storage_adapter.get_history(limit=5)
    assert len(history) == 5
    assert history[0].source == "https://yt.com/9"
    assert history[4].source == "https://yt.com/5"


async def test_legacy_history_schema_migration(tmp_path):
    """Ensures existing databases with a legacy schema are migrated smoothly."""
    import sqlite3

    db_file = tmp_path / "test_legacy_migrate.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE aerich (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            version VARCHAR(255) NOT NULL,
            app VARCHAR(100) NOT NULL,
            content JSON NOT NULL
        );
    """)
    cur.execute(
        "INSERT INTO aerich (version, app, content) VALUES (?, ?, ?)",
        ("0_20260823130641_init.py", "models", "{}"),
    )
    cur.execute("""
        CREATE TABLE history (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            song_title VARCHAR(255) NOT NULL,
            song_artist VARCHAR(255) NOT NULL,
            source VARCHAR(2048) NOT NULL UNIQUE,
            played_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute(
        "INSERT INTO history (song_title, song_artist, source) VALUES (?, ?, ?)",
        ("Legacy Song", "Legacy Artist", "https://yt.com/legacy"),
    )
    conn.commit()
    conn.close()

    adapter = TortoiseStorageAdapter(db_file)
    await adapter.connect()

    history = await adapter.get_history()
    assert len(history) == 1
    assert history[0].title == "Legacy Song"
    assert history[0].artist == "Legacy Artist"
    assert history[0].album == "YouTube Audio"
    assert history[0].duration == 0
    assert history[0].source == "https://yt.com/legacy"

    # Test duplicate insertion to ensure the UNIQUE constraint was removed in the migration.
    s_dup = Song(title="Legacy Song 2", artist="Legacy Artist", source="https://yt.com/legacy")
    await adapter.add_to_history(s_dup)
    assert await HistoryTable.all().count() == 2

    await adapter.disconnect()


async def test_disconnect_checkpoints_wal_and_cleans_files(tmp_path):
    """Ensures disconnect() checkpoints WAL and does not leave -wal or -shm files behind."""
    db_file = tmp_path / "test_wal_clean.db"
    adapter = TortoiseStorageAdapter(db_file)
    await adapter.connect()
    await adapter.add_to_history(Song(title="Title", artist="Artist", source="https://yt.com/wal"))
    await adapter.disconnect()

    wal_file = tmp_path / "test_wal_clean.db-wal"
    shm_file = tmp_path / "test_wal_clean.db-shm"
    assert not wal_file.exists() or wal_file.stat().st_size == 0
    assert not shm_file.exists() or shm_file.stat().st_size == 0
