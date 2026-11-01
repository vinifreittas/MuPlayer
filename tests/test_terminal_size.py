from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.widgets import Label

from muplayer.interface.tui.app import MuPlayer
from muplayer.interface.tui.modals import TerminalTooSmallScreen


def _create_test_app() -> MuPlayer:
    playback = MagicMock()
    playback.set_volume.return_value = 50
    library = MagicMock()
    library.get_playlists = AsyncMock(return_value=[])
    search = MagicMock()
    config = MagicMock()
    config.config.volume = 50
    config.config.language = "en"

    return MuPlayer(
        playback_service=playback,
        library_service=library,
        search_service=search,
        config_service=config,
    )


@pytest.mark.asyncio
async def test_terminal_size_sufficient_does_not_show_warning():
    """Validates that terminals with normal dimensions (>= 80x24) do not show the warning screen."""
    app = _create_test_app()
    async with app.run_test(size=(90, 30)):
        assert not isinstance(app.screen, TerminalTooSmallScreen)


@pytest.mark.asyncio
async def test_terminal_size_too_small_on_start_shows_warning():
    """Validates that starting the player with a terminal smaller than 80x24 shows the warning."""
    app = _create_test_app()
    async with app.run_test(size=(60, 20)):
        assert isinstance(app.screen, TerminalTooSmallScreen)


@pytest.mark.asyncio
async def test_terminal_resize_auto_dismiss_and_reappear():
    """Validates the full cycle: starts small -> expands -> returns to normal -> shrinks -> warning reappears."""
    app = _create_test_app()
    async with app.run_test(size=(60, 20)) as pilot:
        assert isinstance(app.screen, TerminalTooSmallScreen)

        # Expand terminal to valid dimensions
        await pilot.resize_terminal(90, 30)
        await pilot.pause()
        assert not isinstance(app.screen, TerminalTooSmallScreen)

        # Shrink terminal again
        await pilot.resize_terminal(70, 18)
        await pilot.pause()
        assert isinstance(app.screen, TerminalTooSmallScreen)


@pytest.mark.asyncio
async def test_terminal_too_small_updates_dimension_label():
    """Validates that the current dimension label updates while the warning remains visible."""
    app = _create_test_app()
    async with app.run_test(size=(60, 20)) as pilot:
        screen = app.screen
        assert isinstance(screen, TerminalTooSmallScreen)
        label = screen.query_one("#small-term-current", Label)
        assert "60x20" in str(label.render())

        await pilot.resize_terminal(75, 22)
        await pilot.pause()
        label = screen.query_one("#small-term-current", Label)
        assert "75x22" in str(label.render())
