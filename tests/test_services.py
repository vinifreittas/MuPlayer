from unittest.mock import MagicMock

from muplayer.application.playback_service import PlaybackService
from muplayer.domain import Song


def test_playback_service_queue_and_selection():
    """Valida o gerenciamento de fila e seleção de faixa no PlaybackService."""
    mock_audio_port = MagicMock()
    mock_search_port = MagicMock()

    service = PlaybackService(player_api=mock_audio_port, search_api=mock_search_port)

    song1 = Song(id=1, title="Song A", artist="Artist A", source="http://example.com/a")
    song2 = Song(id=2, title="Song B", artist="Artist B", source="http://example.com/b")
    songs = [song1, song2]

    idx = service.set_queue(songs, start_song=song2)
    assert idx == 1
    selected = service.select_track(idx)
    assert selected == song2
    assert service.active_song == song2

    # Seleção de faixa por índice
    selected_first = service.select_track(0)
    assert selected_first == song1
    assert service.active_song == song1

    # Próxima faixa sem shuffle/repeat
    assert service.get_next_index() == 1
