from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.widgets import Label

from muplayer.interface.tui.app import MuPlayer
from muplayer.interface.tui.screens import TerminalTooSmallScreen


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
    """Valida que terminais com dimensões normais (>= 80x24) não exibem a tela de aviso."""
    app = _create_test_app()
    async with app.run_test(size=(90, 30)):
        assert not isinstance(app.screen, TerminalTooSmallScreen)


@pytest.mark.asyncio
async def test_terminal_size_too_small_on_start_shows_warning():
    """Valida que iniciar o player com terminal menor que 80x24 exibe o aviso."""
    app = _create_test_app()
    async with app.run_test(size=(60, 20)):
        assert isinstance(app.screen, TerminalTooSmallScreen)


@pytest.mark.asyncio
async def test_terminal_resize_auto_dismiss_and_reappear():
    """Valida ciclo completo: início pequeno -> amplia -> volta ao normal -> encolhe -> aviso reaparece."""
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
    """Valida se o rótulo de dimensão atual se atualiza ao redimensionar mantendo o aviso."""
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
