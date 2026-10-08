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


async def test_add_to_history_updates_timestamp_and_preserves_id(storage_adapter):
    """Garante que a re-execução da mesma música apenas atualiza o timestamp e preserva o ID."""
    source_link = "https://youtube.com/watch?v=track_one"
    song1 = Song(title="Track One", artist="Artist One", source=source_link)
    await storage_adapter.add_to_history(song1)

    entry_initial = await HistoryTable.filter(source=source_link).first()
    assert entry_initial is not None
    initial_id = entry_initial.id
    initial_timestamp = entry_initial.played_at

    # Toca outra música intermediária
    song2 = Song(title="Track Two", artist="Artist Two", source="https://youtube.com/watch?v=track_two")
    await storage_adapter.add_to_history(song2)

    # Pequena pausa para garantir avanço de timestamp
    await asyncio.sleep(0.01)

    # Toca a música 1 novamente com título atualizado
    song1_updated = Song(title="Track One (Remaster)", artist="Artist One", source=source_link)
    await storage_adapter.add_to_history(song1_updated)

    entry_after = await HistoryTable.filter(source=source_link).first()
    assert entry_after is not None
    # ID deve ser o mesmo (não deletou e recriou)
    assert entry_after.id == initial_id
    # Timestamp deve ter sido atualizado
    assert entry_after.played_at > initial_timestamp
    assert entry_after.song_title == "Track One (Remaster)"

    # Total de registros no banco deve ser 2 (sem duplicatas)
    assert await HistoryTable.all().count() == 2

    # A busca por histórico deve trazer song1 no topo (mais recente)
    history = await storage_adapter.get_history()
    assert len(history) == 2
    assert history[0].source == source_link
    assert history[0].title == "Track One (Remaster)"
    assert history[1].source == "https://youtube.com/watch?v=track_two"


async def test_verification_only_by_source(storage_adapter):
    """Verificação ocorre EXCLUSIVAMENTE por source."""
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

    # 2. Títulos e artistas diferentes, mas mesma URL (source) -> deve ser 1 registro atualizado
    song_renamed = Song(
        title="Queen - Bohemian Rhapsody (Official)",
        artist="Queen Band",
        source="https://youtube.com/watch?v=link_live",
    )
    await storage_adapter.add_to_history(song_renamed)

    history = await storage_adapter.get_history()
    assert len(history) == 2
    assert history[0].source == "https://youtube.com/watch?v=link_live"
    assert history[0].title == "Queen - Bohemian Rhapsody (Official)"


async def test_history_source_unique_constraint(storage_adapter):
    """Garante que a constraint UNIQUE na coluna source rejeita inserções duplicadas diretas."""
    from tortoise.exceptions import IntegrityError

    await HistoryTable.create(song_title="Song 1", song_artist="Artist", source="https://yt.com/unique")
    with pytest.raises(IntegrityError):
        await HistoryTable.create(song_title="Song 2", song_artist="Artist", source="https://yt.com/unique")


async def test_get_history_limit(storage_adapter):
    """Garante respeito ao parâmetro limit e ordenação do mais recente para o mais antigo."""
    for i in range(10):
        song = Song(title=f"Song {i}", artist="Artist", source=f"https://yt.com/{i}")
        await storage_adapter.add_to_history(song)

    history = await storage_adapter.get_history(limit=5)
    assert len(history) == 5
    assert history[0].source == "https://yt.com/9"
    assert history[4].source == "https://yt.com/5"


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
