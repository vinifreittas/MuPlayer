from unittest.mock import AsyncMock, MagicMock

import pytest

from muplayer.interface.tui.app import MuPlayer
from muplayer.interface.tui.widgets import Header, MiniPlayer, Sidebar


@pytest.mark.asyncio
async def test_tui_controllers_event_handling():
    playback_service = MagicMock()
    library_service = MagicMock()
    search_service = MagicMock()
    config_manager = MagicMock()

    playback_service.set_volume.return_value = 50
    playback_service.is_loading = False
    playback_service.toggle_play.return_value = True
    config_manager.config.volume = 50
    config_manager.config.language = "en"
    config_manager.config.efficiency_mode = False

    mock_playlist = MagicMock()
    mock_playlist.songs = []

    library_service.connect = AsyncMock()
    library_service.get_playlists = AsyncMock(return_value=[])
    library_service.get_playlist_by_name = AsyncMock(return_value=mock_playlist)
    search_service.search = MagicMock(return_value=[])

    app = MuPlayer(
        playback_service=playback_service,
        library_service=library_service,
        search_service=search_service,
        config_manager=config_manager,
    )

    async with app.run_test() as pilot:
        header = app.query_one(Header)
        sidebar = app.query_one(Sidebar)
        miniplayer = app.query_one(MiniPlayer)

        # 1. Search submitted event
        header.post_message(Header.SearchSubmitted("test query"))
        await pilot.pause()
        assert search_service.search.call_count == 1
        search_service.search.assert_called_with("test query", limit=config_manager.config.search_limit)

        # 2. Settings opened event
        header.post_message(Header.SettingsCalled())
        await pilot.pause()
        assert len(app._screen_stack) == 2

        # Dismiss screen
        app.pop_screen()
        await pilot.pause()
        assert len(app._screen_stack) == 1

        # 3. Playlist selected event
        sidebar.post_message(Sidebar.PlaylistSelected("Rock"))
        await pilot.pause()
        assert library_service.get_playlist_by_name.call_count == 1
        library_service.get_playlist_by_name.assert_called_with("Rock")

        # 4. MiniPlayer TogglePlay event
        miniplayer.post_message(MiniPlayer.TogglePlay())
        await pilot.pause()
        assert playback_service.toggle_play.call_count == 1
