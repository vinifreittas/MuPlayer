import pytest
from pydantic import ValidationError

from muplayer.domain import AppConfig, Playlist, QueueState, Song


def test_song_methods():
    """Valida métodos e propriedades da entidade Song."""
    song_valid = Song(title="Track 1", artist="Artist", duration=120, source="http://example.com/audio")
    song_empty_source = Song(title="Track 2", artist="Artist", duration=-10, source="  ")
    song_no_source = Song(title="Track 3", artist="Artist", duration=None)

    assert song_valid.duration == 120
    assert song_valid.has_source is True

    assert song_empty_source.duration == 0
    assert song_empty_source.has_source is False

    assert song_no_source.duration == 0
    assert song_no_source.has_source is False


def test_playlist_methods():
    """Valida métodos de cálculo e busca na entidade Playlist."""
    song1 = Song(id=10, title="Song 1", artist="Artist 1", duration=100)
    song2 = Song(id=20, title="Song 2", artist="Artist 2", duration=250)
    playlist = Playlist(name="Favorites", songs=[song1, song2])

    assert playlist.name == "Favorites"
    assert playlist.song_count == 2
    assert playlist.total_duration == 350
    assert playlist.contains_song(10) is True
    assert playlist.contains_song(20) is True
    assert playlist.contains_song(999) is False


def test_queue_state_methods():
    """Valida os métodos puros de navegação e gerenciamento da fila em QueueState."""
    queue = QueueState()
    song1 = Song(id=1, title="Song A", artist="Artist A", source="http://a.com")
    song2 = Song(id=2, title="Song B", artist="Artist B", source="http://b.com")
    songs = [song1, song2]

    # set_songs & select_track
    idx = queue.set_songs(songs, start_song=song2)
    assert idx == 1
    assert queue.select_track(1) == song2
    assert queue.active_song == song2

    # shuffle & repeat toggles
    assert queue.is_shuffling is False
    assert queue.toggle_shuffle() is True
    assert queue.is_shuffling is True

    assert queue.is_repeating is False
    assert queue.toggle_repeat() is True
    assert queue.is_repeating is True
    queue.toggle_shuffle()  # disable shuffle for deterministic repeat test

    # get_next_index using internal state
    assert queue.get_next_index() == 0  # repeating enabled -> loops back to 0

    queue.toggle_repeat()  # disable repeat
    assert queue.get_next_index() is None

    queue.select_track(0)
    assert queue.get_next_index() == 1

    # get_prev_index
    assert queue.get_prev_index(current_time=1) == 0
    assert queue.get_prev_index(current_time=5) == 0  # > 3 seconds keeps current index

    # clear
    queue.clear()
    assert queue.songs == []
    assert queue.current_index == -1
    assert queue.active_song is None


def test_app_config_methods():
    """Valida os métodos e propriedades da entidade AppConfig."""
    config = AppConfig(language="pt", efficiency_mode=False)
    assert config.is_portuguese is True
    assert config.toggle_efficiency_mode() is True
    assert config.efficiency_mode is True

    config_en = AppConfig(language="en")
    assert config_en.is_portuguese is False

    with pytest.raises(ValidationError):
        AppConfig(language="fr")

    with pytest.raises(ValidationError):
        AppConfig(volume=150)
