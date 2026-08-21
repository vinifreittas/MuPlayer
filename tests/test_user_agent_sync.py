from unittest.mock import MagicMock, patch

from muplayer.application.playback_service import PlaybackService
from muplayer.domain import Song
from muplayer.infrastructure.audio.player import MpvBackend, VlcBackend
from muplayer.infrastructure.search.search import DEFAULT_USER_AGENT, SearchAPI


def test_validate_stream_url_success():
    """Testa se validate_stream_url retorna True quando a resposta HTTP é 200 ou 206."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 206
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        assert SearchAPI().extract_audio_url is not None
        from muplayer.infrastructure.search.search import validate_stream_url

        assert validate_stream_url("https://googlevideo.com/valid", user_agent="UA/1.0") is True


def test_validate_stream_url_failure():
    """Testa se validate_stream_url retorna False quando há erro HTTP ou exceção de conexão."""
    with patch("urllib.request.urlopen", side_effect=Exception("403 Forbidden")):
        from muplayer.infrastructure.search.search import validate_stream_url

        assert validate_stream_url("https://googlevideo.com/expired", user_agent="UA/1.0") is False


def test_search_api_extract_audio_url_returns_user_agent():
    """Testa se SearchAPI extrai a URL do áudio e o User-Agent correspondente."""
    search_api = SearchAPI()
    mock_info = {
        "url": "https://googlevideo.com/videoplayback?id=123",
        "http_headers": {"User-Agent": "TestUserAgent/1.0"},
    }

    with (
        patch("yt_dlp.YoutubeDL") as mock_ydl_cls,
        patch("muplayer.infrastructure.search.search.validate_stream_url", return_value=True),
    ):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        url, user_agent = search_api.extract_audio_url("https://youtube.com/watch?v=123")

        assert url == "https://googlevideo.com/videoplayback?id=123"
        assert user_agent == "TestUserAgent/1.0"


def test_search_api_extract_audio_url_fallback_user_agent():
    """Testa se SearchAPI utiliza o User-Agent padrão quando http_headers não contém a chave."""
    search_api = SearchAPI()
    mock_info = {
        "url": "https://googlevideo.com/videoplayback?id=456",
    }

    with (
        patch("yt_dlp.YoutubeDL") as mock_ydl_cls,
        patch("muplayer.infrastructure.search.search.validate_stream_url", return_value=True),
    ):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        url, user_agent = search_api.extract_audio_url("https://youtube.com/watch?v=456")

        assert url == "https://googlevideo.com/videoplayback?id=456"
        assert user_agent == DEFAULT_USER_AGENT


def test_playback_service_invalidates_cached_url():
    """Testa se PlaybackService limpa cache quando invalidate_audio_cache é invocado."""
    mock_cache = MagicMock()
    mock_search_port = MagicMock()
    mock_audio_port = MagicMock()
    playback_service = PlaybackService(player_api=mock_audio_port, search_api=mock_search_port, cache=mock_cache)

    playback_service.invalidate_audio_cache("https://youtube.com/watch?v=789")

    mock_cache.delete.assert_called_once_with("yt:audio_url:https://youtube.com/watch?v=789")


def test_mpv_backend_sets_user_agent():
    """Testa se MpvBackend aplica a opção user-agent no player mpv."""
    with patch.dict("sys.modules", {"mpv": MagicMock()}):
        mpv_backend = MpvBackend()
        mpv_backend._player = MagicMock()

        mpv_backend.play("https://stream.url", user_agent="CustomMPVUA/2.0")

        mpv_backend._player.__setitem__.assert_called_once_with("user-agent", "CustomMPVUA/2.0")
        mpv_backend._player.play.assert_called_once_with("https://stream.url")


def test_vlc_backend_sets_user_agent():
    """Testa se VlcBackend adiciona a opção :http-user-agent na mídia VLC."""
    with patch.dict("sys.modules", {"vlc": MagicMock()}):
        vlc_backend = VlcBackend()
        mock_instance = MagicMock()
        mock_media = MagicMock()
        mock_instance.media_new.return_value = mock_media

        vlc_backend._instance = mock_instance
        vlc_backend._player = MagicMock()

        vlc_backend.play("https://stream.url", user_agent="CustomVLCUA/3.0")

        mock_instance.media_new.assert_called_once_with("https://stream.url")
        mock_media.add_option.assert_called_once_with(":http-user-agent=CustomVLCUA/3.0")
        vlc_backend._player.set_media.assert_called_once_with(mock_media)
        vlc_backend._player.play.assert_called_once()


def test_playback_service_forwards_user_agent_to_player():
    """Testa se PlaybackService.prepare_and_play_active repassa o User-Agent para o PlayerAPI."""
    mock_audio_port = MagicMock()
    mock_search_port = MagicMock()

    playback_service = PlaybackService(mock_audio_port, search_api=mock_search_port)

    song = Song(title="Test Song", artist="Test Artist", source="https://youtube.com/watch?v=abc")
    playback_service.set_queue([song])
    playback_service.select_track(0)

    mock_search_port.extract_audio_url.return_value = (
        "https://googlevideo.com/stream",
        "Mozilla/5.0 TestUA",
    )
    mock_audio_port.play.return_value = True

    result_url = playback_service.prepare_and_play_active()

    assert result_url == "https://googlevideo.com/stream"
    mock_audio_port.play.assert_called_once_with("https://googlevideo.com/stream", user_agent="Mozilla/5.0 TestUA")
