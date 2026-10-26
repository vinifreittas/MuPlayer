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
    """Garante que a re-execução da mesma música gera novos registros de log e o get_history deduplica pela última ocorrência."""
    source_link = "https://youtube.com/watch?v=track_one"
    song1 = Song(title="Track One", artist="Artist One", album="Album A", duration=180, source=source_link)
    await storage_adapter.add_to_history(song1)

    entry_initial = await HistoryTable.filter(source=source_link).first()
    assert entry_initial is not None
    initial_id = entry_initial.id
    initial_timestamp = entry_initial.played_at

    # Toca outra música intermediária
    song2 = Song(
        title="Track Two",
        artist="Artist Two",
        album="Album B",
        duration=210,
        source="https://youtube.com/watch?v=track_two",
    )
    await storage_adapter.add_to_history(song2)

    # Pequena pausa para garantir avanço de timestamp
    await asyncio.sleep(0.01)

    # Toca a música 1 novamente com título atualizado
    song1_updated = Song(
        title="Track One (Remaster)", artist="Artist One", album="Album A", duration=185, source=source_link
    )
    await storage_adapter.add_to_history(song1_updated)

    # Total de registros no banco de dados deve ser 3 (log cumulativo de execuções)
    assert await HistoryTable.all().count() == 3

    # As 2 ocorrências de track_one devem existir como linhas distintas
    track_one_entries = await HistoryTable.filter(source=source_link).order_by("played_at")
    assert len(track_one_entries) == 2
    assert track_one_entries[0].id == initial_id
    assert track_one_entries[1].id != initial_id
    assert track_one_entries[1].played_at > initial_timestamp
    assert track_one_entries[1].title == "Track One (Remaster)"

    # A busca por histórico inteligente deve trazer song1 no topo (mais recente) e deduplicada
    history = await storage_adapter.get_history()
    assert len(history) == 2
    assert history[0].source == source_link
    assert history[0].title == "Track One (Remaster)"
    assert history[0].duration == 185
    assert history[1].source == "https://youtube.com/watch?v=track_two"
    assert history[1].duration == 210


async def test_verification_only_by_source(storage_adapter):
    """Verificação e deduplicação ocorrem EXCLUSIVAMENTE por source."""
    # 1. Títulos e artistas idênticos, mas com URLs (sources) diferentes -> devem ser 2 registros distintos
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

    # 2. Títulos e artistas diferentes, mas mesma URL (source) -> log tem 3 rows, consulta traz 2 deduplicadas
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
    """Garante que a restrição UNIQUE foi removida e que metadados completos são preservados."""
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
    """Garante respeito ao parâmetro limit e ordenação do mais recente para o mais antigo."""
    for i in range(10):
        song = Song(title=f"Song {i}", artist="Artist", source=f"https://yt.com/{i}")
        await storage_adapter.add_to_history(song)

    history = await storage_adapter.get_history(limit=5)
    assert len(history) == 5
    assert history[0].source == "https://yt.com/9"
    assert history[4].source == "https://yt.com/5"


async def test_legacy_history_schema_migration(tmp_path):
    """Garante que bancos de dados existentes com schema legado são migrados suavemente."""
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

    # Testa inserção duplicada para garantir que a constraint UNIQUE foi removida no migration
    s_dup = Song(title="Legacy Song 2", artist="Legacy Artist", source="https://yt.com/legacy")
    await adapter.add_to_history(s_dup)
    assert await HistoryTable.all().count() == 2

    await adapter.disconnect()


async def test_disconnect_checkpoints_wal_and_cleans_files(tmp_path):
    """Garante que o disconnect() executa checkpoint do WAL e não deixa arquivos -wal ou -shm soltos."""
    db_file = tmp_path / "test_wal_clean.db"
    adapter = TortoiseStorageAdapter(db_file)
    await adapter.connect()
    await adapter.add_to_history(Song(title="Title", artist="Artist", source="https://yt.com/wal"))
    await adapter.disconnect()

    wal_file = tmp_path / "test_wal_clean.db-wal"
    shm_file = tmp_path / "test_wal_clean.db-shm"
    assert not wal_file.exists() or wal_file.stat().st_size == 0
    assert not shm_file.exists() or shm_file.stat().st_size == 0
