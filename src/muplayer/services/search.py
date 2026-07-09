import inspect
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

import yt_dlp

from muplayer.models import Song

logger = logging.getLogger(__name__)

YTDL_BASE_OPTS: dict[str, Any] = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "js_runtimes": {"quickjs": {}},
    "source_address": "0.0.0.0",
}


def cache_result(namespace: str, expire_seconds: int = 3600):
    """Decorator to cache method results using a dedicated namespace."""

    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not getattr(self, "cache", None):
                return func(self, *args, **kwargs)

            sig = inspect.signature(func)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()

            key_parts = []
            for param_name, param_value in bound_args.arguments.items():
                if param_name == "self":
                    continue
                key_parts.append(f"{param_name}:{param_value}")

            cache_key = f"{namespace}:{'_'.join(key_parts)}"

            if self.cache.exists(cache_key):
                logger.debug(f"Cache hit for key: {cache_key}")
                return self.cache.get(cache_key)

            result = func(self, *args, **kwargs)
            self.cache.set(cache_key, result, expire=expire_seconds)
            return result

        return wrapper

    return decorator


class SearchAPI:
    """Handles YouTube interactions via yt-dlp as an internal service layer."""

    def __init__(self, cache_client: Any = None, base_opts: dict[str, Any] | None = None) -> None:
        self.cache = cache_client
        self.base_opts = base_opts or YTDL_BASE_OPTS
        logger.debug("SearchAPI initialized.")

    def _get_instance(self, extra_opts: dict[str, Any] | None = None) -> yt_dlp.YoutubeDL:
        config = {**self.base_opts, **(extra_opts or {})}
        return yt_dlp.YoutubeDL(config)

    @cache_result(namespace="yt:search", expire_seconds=3600 * 5)
    def search(self, query: str, max_results: int) -> list[Song]:
        """Search for songs on YouTube."""
        logger.info(f"Searching for '{query}' (max_results={max_results})")
        search_opts = {"default_search": f"ytsearch{max_results}", "extract_flat": "in_playlist"}

        try:
            with self._get_instance(search_opts) as ydl:
                info = ydl.extract_info(query, download=False) or {}
                entries = info.get("entries", [])
                logger.info(f"Found {len(entries)} results for '{query}'")

                return [
                    Song(
                        title=e.get("title", "Unknown Track"),
                        artist=e.get("uploader") or e.get("artist") or "Unknown Artist",
                        album="YouTube Audio",
                        duration=int(float(e.get("duration") or 0)),
                        source=e.get("url") or e.get("webpage_url"),
                    )
                    for e in entries
                    if e
                ]
        except Exception as e:
            logger.error(f"Unexpected YouTube search error for query '{query}': {e}", exc_info=True)
            return []

    @cache_result(namespace="yt:audio_url", expire_seconds=3600 * 60)
    def extract_audio_url(self, video_url: str) -> str | None:
        """Extract audio URL from a video URL."""
        logger.info(f"Extracting audio URL for: {video_url}")
        try:
            with self._get_instance() as ydl_final:
                info = ydl_final.extract_info(video_url, download=False)
                url = info.get("url") if info else None
                if url:
                    logger.debug("Extracted audio URL successfully.")
                else:
                    logger.warning(f"Could not extract audio URL for: {video_url}")
                return url
        except Exception as e:
            logger.error(f"Unexpected audio URL extraction error for {video_url}: {e}", exc_info=True)
            return None
