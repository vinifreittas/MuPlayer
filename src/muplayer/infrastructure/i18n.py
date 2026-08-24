"""
Lightweight i18n module for MuPlayer. (DT-25)

Design decisions:
- Two supported locales: "en" (English, default) and "pt" (Portuguese).
- Strings are stored as plain dicts — no external dependency needed.
- Access pattern: `t("key")` returns the translated string for the active locale.
- `set_locale(language_code)` updates the active locale at runtime.
"""

from functools import lru_cache
from typing import Any

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Playback
        "no_active_song": "No song is currently selected.",
        "playback_engine_error": "Failed to start playback in the audio engine.",
        "playback_missing_url": "Invalid or missing song URL.",
        "no_track_playing": "No track playing",
        # Playlist
        "no_playlist_selected": "No playlist selected.",
        "song_added_to_playlist": "'{title}' added to '{playlist}'.",
        "song_add_failed": "Failed to add song to '{playlist}'.",
        "playlist_create_failed": "Failed to create playlist '{playlist}'.",
        # Search
        "search_no_results": "No results found for '{query}'.",
        "search_network_error": "Network error while searching for '{query}'. Check your connection.",
        # Header Widget
        "search_placeholder": "🔍 Search for songs, artists, podcasts...",
        "settings_btn": "⚙️ Settings",
        # Sidebar Widget
        "sidebar_library": "LIBRARY",
        "sidebar_home": "🏠 Home",
        "sidebar_discover": "🔍 Discover",
        "sidebar_radio": "📻 Radio",
        "sidebar_playlists": "PLAYLISTS",
        # SongList Widget
        "songs_title": "Songs",
        "play_all_btn": "▶ Play All",
        # Configurations Screen
        "config_title": "Application Settings",
        "config_search_limit": "Max Search Results:",
        "config_language": "Language / Idioma:",
        "config_efficiency_mode": "Efficiency Mode:",
        "config_close": "Close",
        # SelectPlaylistModal
        "modal_add_title": "🎵 Add to Playlist",
        "modal_existing_playlists": "Select an existing playlist:",
        "modal_no_playlists": "No playlists yet. Create one below.",
        "modal_create_new": "Or create a new playlist:",
        "modal_new_placeholder": "New playlist name...",
        "modal_btn_add": "Add",
        "modal_btn_cancel": "Cancel",
        # General
        "update_outside_venv": (
            "Warning: You are not running inside a virtual environment.\n"
            "It is strongly recommended to run updates inside a venv."
        ),
    },
    "pt": {
        # Playback
        "no_active_song": "Nenhuma música selecionada.",
        "playback_engine_error": "Falha ao iniciar reprodução no engine de áudio.",
        "playback_missing_url": "URL da música inválida ou ausente.",
        "no_track_playing": "Nenhuma música tocando",
        # Playlist
        "no_playlist_selected": "Nenhuma playlist selecionada.",
        "song_added_to_playlist": "'{title}' adicionada a '{playlist}'.",
        "song_add_failed": "Falha ao adicionar música a '{playlist}'.",
        "playlist_create_failed": "Falha ao criar playlist '{playlist}'.",
        # Search
        "search_no_results": "Nenhum resultado encontrado para '{query}'.",
        "search_network_error": "Erro de rede ao buscar '{query}'. Verifique sua conexão.",
        # Header Widget
        "search_placeholder": "🔍 Buscar músicas, artistas, podcasts...",
        "settings_btn": "⚙️ Configurações",
        # Sidebar Widget
        "sidebar_library": "BIBLIOTECA",
        "sidebar_home": "🏠 Início",
        "sidebar_discover": "🔍 Descobrir",
        "sidebar_radio": "📻 Rádio",
        "sidebar_playlists": "PLAYLISTS",
        # SongList Widget
        "songs_title": "Músicas",
        "play_all_btn": "▶ Tocar Todas",
        # Configurations Screen
        "config_title": "Configurações do Aplicativo",
        "config_search_limit": "Limite de Busca:",
        "config_language": "Idioma / Language:",
        "config_efficiency_mode": "Modo Eficiência:",
        "config_close": "Fechar",
        # SelectPlaylistModal
        "modal_add_title": "🎵 Adicionar à Playlist",
        "modal_existing_playlists": "Selecione uma playlist existente:",
        "modal_no_playlists": "Nenhuma playlist. Crie uma abaixo.",
        "modal_create_new": "Ou crie uma nova playlist:",
        "modal_new_placeholder": "Nome da nova playlist...",
        "modal_btn_add": "Adicionar",
        "modal_btn_cancel": "Cancelar",
        # General
        "update_outside_venv": (
            "Atenção: Você não está dentro de um ambiente virtual (venv).\n"
            "É altamente recomendado executar atualizações dentro de um venv."
        ),
    },
}

_active_locale: str = "en"
_active_strings: dict[str, str] = _TRANSLATIONS["en"]


@lru_cache(maxsize=512)
def _get_raw_translation(key: str, locale: str) -> str:
    strings = _TRANSLATIONS.get(locale, _TRANSLATIONS["en"])
    return strings.get(key) or _TRANSLATIONS["en"].get(key) or key


def set_locale(language_code: str) -> None:
    """
    Set the active translation locale. Falls back to 'en' for unsupported codes.
    """
    global _active_locale, _active_strings
    _active_locale = language_code if language_code in _TRANSLATIONS else "en"
    _active_strings = _TRANSLATIONS[_active_locale]


def t(key: str, **kwargs: Any) -> str:
    """
    Return the translated string for the given key in the active locale.

    - Falls back to English if the key is missing in the active locale.
    - Falls back to the raw key string if missing in both.
    - Supports str.format_map for named placeholders, e.g. t("song_added", title="X", playlist="Y").
    - Accepts any value type for interpolation (int, float, str, etc.).
    """
    raw = _get_raw_translation(key, _active_locale)
    if kwargs:
        try:
            return raw.format_map(kwargs)
        except KeyError:
            return raw
    return raw
