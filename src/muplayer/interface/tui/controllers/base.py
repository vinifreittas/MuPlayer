from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from muplayer.application.config_service import ConfigService
    from muplayer.application.library_service import LibraryService
    from muplayer.application.playback_service import PlaybackService
    from muplayer.application.search_service import SearchService

logger = logging.getLogger(__name__)


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


def safe_call_from_thread(target: Any, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """Safely dispatches call_from_thread only if the target component is running."""
    if not getattr(target, "is_running", True):
        logger.debug("Target component is not running; suppressing call_from_thread.")
        return
    try:
        target.call_from_thread(func, *args, **kwargs)
    except RuntimeError as e:
        logger.debug("call_from_thread suppressed due to RuntimeError: %s", e)
