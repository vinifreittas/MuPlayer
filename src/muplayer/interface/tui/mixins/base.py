from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def safe_call_from_thread(target: Any, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """Safely dispatches call_from_thread only if the target component is running."""
    if not getattr(target, "is_running", True):
        logger.debug("Target component is not running; suppressing call_from_thread.")
        return
    try:
        target.call_from_thread(func, *args, **kwargs)
    except RuntimeError as e:
        logger.debug("call_from_thread suppressed due to RuntimeError: %s", e)
