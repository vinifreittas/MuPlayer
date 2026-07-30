"""
Unit tests for Phase 5 utility functions.

Coverage:
- format_time (DT-14): HH:MM:SS, MM:SS, negative clamping, zero
- i18n t() and set_locale() (DT-25): locale switching, key fallback, format placeholders
"""

import pytest

from muplayer.interface.helpers import format_time
from muplayer.utils.i18n import set_locale, t

# ---------------------------------------------------------------------------
# format_time (DT-14)
# ---------------------------------------------------------------------------


def test_format_time_seconds_only():
    assert format_time(7) == "0:07"


def test_format_time_minutes_and_seconds():
    assert format_time(187) == "3:07"


def test_format_time_exact_minute():
    assert format_time(60) == "1:00"


def test_format_time_one_hour():
    assert format_time(3600) == "1:00:00"


def test_format_time_over_one_hour():
    assert format_time(3_661) == "1:01:01"


def test_format_time_negative_clamped_to_zero():
    assert format_time(-5) == "0:00"


def test_format_time_zero():
    assert format_time(0) == "0:00"


def test_format_time_long_duration():
    # 2h 30m 45s = 9045s
    assert format_time(9_045) == "2:30:45"


# ---------------------------------------------------------------------------
# i18n (DT-25)
# ---------------------------------------------------------------------------


def test_t_returns_english_by_default():
    set_locale("en")
    result = t("no_active_song")
    assert result == "No song is currently selected."


def test_t_returns_portuguese_when_locale_is_pt():
    set_locale("pt")
    result = t("no_active_song")
    assert result == "Nenhuma música selecionada."
    set_locale("en")  # reset for subsequent tests


def test_t_with_format_placeholders():
    set_locale("en")
    result = t("song_added_to_playlist", title="My Song", playlist="Rock")
    assert "My Song" in result
    assert "Rock" in result


def test_t_falls_back_to_english_for_unknown_locale():
    set_locale("fr")  # not supported
    result = t("no_active_song")
    assert result == "No song is currently selected."
    set_locale("en")


def test_t_returns_key_for_missing_key():
    set_locale("en")
    result = t("this_key_does_not_exist")
    assert result == "this_key_does_not_exist"


def test_t_search_no_results_with_query():
    set_locale("pt")
    result = t("search_no_results", query="jazz")
    assert "jazz" in result
    set_locale("en")


# ---------------------------------------------------------------------------
# Modal Screen Scoping & NoMatches Guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_playback_progress_during_modal_screen():
    from muplayer.app import MuPlayer
    from muplayer.interface.screens import SelectPlaylistModal
    from muplayer.models import Song

    app = MuPlayer(player_engine="mpv")
    async with app.run_test() as pilot:
        app.is_playing = True
        app.active_song = Song(title="Test", artist="Artist", album="Album", duration=300)

        # Push modal screen so MiniPlayer is no longer on the active DOM screen
        app.push_screen(SelectPlaylistModal([]))
        await pilot.pause()

        # Must not raise textual.css.query.NoMatches exception
        app._update_playback_progress()
        assert app.current_time > 0


@pytest.mark.asyncio
async def test_sidebar_playlist_selection():
    from muplayer.app import MuPlayer
    from muplayer.interface.widgets import Sidebar

    app = MuPlayer(player_engine="mpv")
    async with app.run_test() as pilot:
        sidebar = app.query_one(Sidebar)
        sidebar.playlist_names = ["Rock Classics", "Jazz Hits"]
        await pilot.pause()

        # Simulate selecting the first playlist
        from textual.widgets import ListView

        list_view = sidebar.query_one("#playlist-items", ListView)
        assert len(list_view.children) == 2

        selected_event = ListView.Selected(list_view, list_view.children[0])
        sidebar._on_playlist_click(selected_event)
        await pilot.pause()


@pytest.mark.asyncio
async def test_live_language_switching_on_mounted_widgets():
    from muplayer.app import MuPlayer
    from muplayer.interface.widgets import Header, Sidebar, SongList
    from muplayer.utils.i18n import set_locale

    app = MuPlayer(player_engine="mpv")
    async with app.run_test() as pilot:
        set_locale("en")
        app._refresh_ui_translations()
        await pilot.pause()

        assert app.query_one(SongList).query_one("#songs-header-title").renderable == "Songs"

        # Switch to Portuguese live
        set_locale("pt")
        app._refresh_ui_translations()
        await pilot.pause()

        assert app.query_one(SongList).query_one("#songs-header-title").renderable == "Músicas"
        assert app.query_one(Header).query_one("#settings-btn").renderable == "⚙️ Configurações"
        assert app.query_one(Sidebar).query_one("#lib-title").renderable == "BIBLIOTECA"

        # Reset back to English
        set_locale("en")
        app._refresh_ui_translations()
        await pilot.pause()
