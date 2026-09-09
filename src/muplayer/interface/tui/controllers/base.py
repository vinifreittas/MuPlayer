from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from muplayer.application.config_service import ConfigService
    from muplayer.application.library_service import LibraryService
    from muplayer.application.playback_service import PlaybackService
    from muplayer.application.search_service import SearchService


class ControllerContext(Protocol):
    """Protocol defining required application services and reactive state for TUI mixins."""

    playback_service: PlaybackService
    library_service: LibraryService
    search_service: SearchService
    config_service: ConfigService

    is_playing: bool
    current_time: int
    is_shuffling: bool
    is_repeating: bool
    update_timer: Any
