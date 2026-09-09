from unittest.mock import MagicMock

from muplayer.application.playback_service import PlaybackService
from muplayer.domain import Song


def test_playback_service_queue_and_selection():
    """Valida o gerenciamento de fila e seleção de faixa no PlaybackService."""
    mock_audio_port = MagicMock()
    mock_media_port = MagicMock()

    service = PlaybackService(audio_player=mock_audio_port, media_provider=mock_media_port)

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


def test_config_service_updates_and_volume():
    """Valida o funcionamento do ConfigService e atualização de configurações/volume."""
    from muplayer.application.config_service import ConfigService
    from muplayer.domain.config import AppConfig

    mock_config_port = MagicMock()
    mock_config_port.get.return_value = AppConfig(volume=50, language="en", search_limit=15)

    config_service = ConfigService(config_port=mock_config_port)

    assert config_service.config.volume == 50

    # Updating volume clamped
    clamped = config_service.update_volume(120)
    assert clamped == 100
    mock_config_port.update.assert_called_with(volume=100)

    # Updating settings with side-effect (language)
    config_service.update(language="pt", search_limit=25)
    mock_config_port.update.assert_called_with(language="pt", search_limit=25)
