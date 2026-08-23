import logging
import time
import urllib.request
from typing import Any

import yt_dlp

from muplayer.application.ports import SearchPort
from muplayer.domain import Song

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0

YTDL_BASE_OPTS: dict[str, Any] = {
    "quiet": True,
    "no_warnings": True,
    "source_address": "0.0.0.0",
    "skip_download": True,
}


def validate_stream_url(url: str, timeout: float = 2.0) -> bool:
    """
    Performs a lightweight HTTP check to verify if a direct stream URL is still valid.
    Sends a GET request with 'Range: bytes=0-0' or HEAD request.
    """
    if not url:
        return False

    headers = {"Range": "bytes=0-0"}

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 206, 301, 302)
    except Exception as e:
        logger.debug(f"HTTP Range GET validation failed for {url}: {e}")

    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 206, 301, 302)
    except Exception as e:
        logger.debug(f"HTTP HEAD validation failed for {url}: {e}")
        return False


class SearchAPI(SearchPort):
    """Handles YouTube interactions via persistent yt-dlp instances."""

    def __init__(
        self,
        js_runtime: dict[str, dict] | None = None,
        browser: str = "firefox",
        base_opts: dict[str, Any] | None = None,
    ) -> None:
        self.base_opts = base_opts or YTDL_BASE_OPTS

        search_opts = {
            **self.base_opts,
            "extract_flat": "in_playlist",
        }

        extractor_opts = {
            **self.base_opts,
            "format": "bestaudio/best",
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "noplaylist": True,
            "js_runtimes": js_runtime,
            "cookiesfrombrowser": (browser,),
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "mweb"],
                    "skip": ["dash", "hls", "translated_subs"],
                }
            },
        }

        self._search_ydl = yt_dlp.YoutubeDL(search_opts)
        self._extractor_ydl = yt_dlp.YoutubeDL(extractor_opts)
        logger.debug("SearchAPI initialized with specialized YoutubeDL instances.")

    def close(self) -> None:
        """Encerra e limpa os recursos das instâncias do yt-dlp."""
        try:
            if hasattr(self, "_search_ydl"):
                self._search_ydl.close()
            if hasattr(self, "_extractor_ydl"):
                self._extractor_ydl.close()
            logger.debug("SearchAPI closed cleanly.")
        except Exception as e:
            logger.warning(f"Error closing YoutubeDL instances: {e}")

    def search(self, query: str, max_results: int = 15) -> list[Song]:
        """Search for songs on YouTube using the lightweight search instance."""
        logger.info(f"Searching for '{query}' (max_results={max_results})")
        search_query = f"ytsearch{max_results}:{query}"

        try:
            info = self._search_ydl.extract_info(search_query, download=False) or {}
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

    def extract_audio_url(self, video_url: str) -> str | None:
        """Extract a direct audio stream URL using the extractor instance with cookies and JS support."""
        logger.info(f"Extracting audio URL for: {video_url}")
        last_exception: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                info = self._extractor_ydl.extract_info(video_url, download=False)
                url = info.get("url") if info else None
                if url:
                    if validate_stream_url(url):
                        logger.debug(f"Audio URL extracted and validated successfully (attempt {attempt}).")
                        return url

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
                return None

        logger.error(
            f"Failed to extract audio URL for {video_url} after {MAX_RETRIES} attempts. Last error: {last_exception}"
        )
        return None
