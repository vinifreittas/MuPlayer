"""
SearchAPI — YouTube search and audio URL extraction via yt-dlp.

Design decisions:
- DT-01: Audio URL cache TTL is 3600s (1 hour). Cached automatically via @cache_result.
  Invalidation helper `invalidate_audio_url_cache(video_url)` clears cached keys on failure.
- DT-03: YoutubeDL instances are created per-operation inside `with` context managers
  to guarantee thread-safety during concurrent worker execution.
- DT-05: `extract_audio_url` retries up to MAX_RETRIES times with linear backoff for transient network errors.
"""

import inspect
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

import yt_dlp

from muplayer.models import Song

logger = logging.getLogger(__name__)

# Retry configuration for transient network errors (DT-05)
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0

YTDL_BASE_OPTS: dict[str, Any] = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "js_runtimes": {"quickjs": {}},
    "source_address": "0.0.0.0",
}


def cache_result(namespace: str, expire_seconds: int = 3600):
    """Decorator to cache non-None method results using a dedicated namespace."""

    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not getattr(self, "cache", None):
                return func(self, *args, **kwargs)

            sig = inspect.signature(func)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()

            key_parts = [
                f"{param_name}:{param_value}"
                for param_name, param_value in bound_args.arguments.items()
                if param_name != "self"
            ]
            cache_key = f"{namespace}:{'_'.join(key_parts)}"

            if self.cache.exists(cache_key):
                logger.debug(f"Cache hit for key: {cache_key}")
                return self.cache.get(cache_key)

            result = func(self, *args, **kwargs)
            if result is not None:
                self.cache.set(cache_key, result, expire=expire_seconds)
            return result

        return wrapper

    return decorator


class SearchAPI:
    """Handles YouTube interactions via yt-dlp as an internal service layer."""

    def __init__(self, cache_client: Any = None, base_opts: dict[str, Any] | None = None) -> None:
        self.cache = cache_client
        self.base_opts = base_opts or YTDL_BASE_OPTS
        logger.debug("SearchAPI initialized (per-operation yt-dlp instances for thread-safety).")

    def close(self) -> None:
        """No-op: per-operation instances are closed via context managers."""
        logger.debug("SearchAPI closed.")

    def invalidate_audio_url_cache(self, video_url: str) -> None:
        """Removes a stale audio URL from the cache so the next call re-extracts it (DT-01)."""
        if self.cache:
            cache_key = f"yt:audio_url:video_url:{video_url}"
            self.cache.delete(cache_key)
            logger.debug(f"Invalidated cached audio URL for: {video_url}")

    @cache_result(namespace="yt:search", expire_seconds=300)  # 5 minutes
    def search(self, query: str, max_results: int) -> list[Song]:
        """
        Search for songs on YouTube.

        DT-03: Creates a fresh YoutubeDL instance per call inside a context manager,
        ensuring this method is safe to call from concurrent threads.
        """
        logger.info(f"Searching for '{query}' (max_results={max_results})")
        search_query = f"ytsearch{max_results}:{query}"
        opts = {**self.base_opts, "extract_flat": "in_playlist"}

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search_query, download=False) or {}
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

    @cache_result(namespace="yt:audio_url", expire_seconds=3600)  # 1 hour (DT-01)
    def extract_audio_url(self, video_url: str) -> str | None:
        """
        Extract a direct audio stream URL from a YouTube video URL.

        DT-01: TTL is 1h. Cached automatically via @cache_result.
        DT-03: Uses a per-call YoutubeDL context manager for thread-safety.
        DT-05: Retries up to MAX_RETRIES times on transient errors with linear backoff.
        """
        logger.info(f"Extracting audio URL for: {video_url}")
        last_exception: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with yt_dlp.YoutubeDL(self.base_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)

                url = info.get("url") if info else None
                if url:
                    logger.debug(f"Audio URL extracted successfully (attempt {attempt}).")
                    return url

                logger.warning(f"Could not extract audio URL for: {video_url} (attempt {attempt})")

            except yt_dlp.utils.DownloadError as e:
                last_exception = e
                logger.warning(f"yt-dlp DownloadError on attempt {attempt}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * attempt
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"Non-retriable error extracting audio URL for {video_url}: {e}", exc_info=True)
                return None

        logger.error(
            f"Failed to extract audio URL for {video_url} after {MAX_RETRIES} attempts. Last error: {last_exception}"
        )
        return None
