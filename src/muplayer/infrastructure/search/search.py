"""
SearchAPI — YouTube search and audio URL extraction via yt-dlp.

Design decisions:
- DT-03: YoutubeDL instances are created per-operation inside `with` context managers
  to guarantee thread-safety during concurrent worker execution.
- DT-05: `extract_audio_url` retries up to MAX_RETRIES times with linear backoff for transient network errors.
"""

import logging
import time
import urllib.request
from typing import Any

import yt_dlp

from muplayer.application.ports import SearchPort
from muplayer.domain import Song

logger = logging.getLogger(__name__)

# Retry configuration for transient network errors (DT-05)
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

YTDL_BASE_OPTS: dict[str, Any] = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "js_runtimes": {"quickjs": {}},
    "source_address": "0.0.0.0",
    "useragent": DEFAULT_USER_AGENT,
}


def validate_stream_url(url: str, user_agent: str | None = None, timeout: float = 2.0) -> bool:
    """
    Performs a lightweight HTTP check to verify if a direct stream URL is still valid.
    Sends a GET request with 'Range: bytes=0-0' or HEAD request.
    """
    if not url:
        return False

    ua = user_agent or DEFAULT_USER_AGENT
    headers = {"User-Agent": ua, "Range": "bytes=0-0"}

    # Try Range GET request first (most reliable for CDN media streams)
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 206, 301, 302)
    except Exception as e:
        logger.debug(f"HTTP Range GET validation failed for {url}: {e}")

    # Fallback to HEAD request if GET fails
    try:
        req = urllib.request.Request(url, headers={"User-Agent": ua}, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 206, 301, 302)
    except Exception as e:
        logger.debug(f"HTTP HEAD validation failed for {url}: {e}")
        return False


class SearchAPI(SearchPort):
    """Handles YouTube interactions via yt-dlp as an internal service layer."""

    def __init__(self, base_opts: dict[str, Any] | None = None) -> None:
        self.base_opts = base_opts or YTDL_BASE_OPTS
        logger.debug("SearchAPI initialized (per-operation yt-dlp instances for thread-safety).")

    def close(self) -> None:
        """No-op: per-operation instances are closed via context managers."""
        logger.debug("SearchAPI closed.")

    def search(self, query: str, max_results: int = 15) -> list[Song]:
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

    def extract_audio_url(self, video_url: str) -> tuple[str | None, str | None]:
        """
        Extract a direct audio stream URL and User-Agent from a YouTube video URL.

        Validates fresh URLs via lightweight HTTP Range GET/HEAD request.
        """
        logger.info(f"Extracting audio URL for: {video_url}")
        last_exception: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with yt_dlp.YoutubeDL(self.base_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)

                url = info.get("url") if info else None
                if url:
                    headers = info.get("http_headers") or {}
                    user_agent = (
                        headers.get("User-Agent")
                        or info.get("user_agent")
                        or self.base_opts.get("useragent")
                        or DEFAULT_USER_AGENT
                    )

                    # Validate fresh URL
                    if validate_stream_url(url, user_agent=user_agent):
                        logger.debug(f"Audio URL extracted and validated successfully (attempt {attempt}).")
                        return url, user_agent

                    logger.warning(f"Extracted audio URL failed validation for: {video_url} (attempt {attempt})")

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
                return None, None

        logger.error(
            f"Failed to extract audio URL for {video_url} after {MAX_RETRIES} attempts. Last error: {last_exception}"
        )
        return None, None
