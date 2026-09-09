import logging
import time
from typing import Any

import yt_dlp

from muplayer.application.ports import MediaPort, SearchPort
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


class YouTubeMediaProvider(SearchPort, MediaPort):
    """Handles YouTube interactions (catalog search and audio stream extraction) via persistent yt-dlp instances."""

    def __init__(
        self,
        js_runtime: dict[str, dict],
        browser: str,
        base_opts: dict[str, Any] | None = None,
    ) -> None:
        if not js_runtime:
            raise ValueError(
                "A valid JavaScript runtime (quickjs, node, deno, or bun) is required for YouTubeMediaProvider."
            )

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
        logger.debug("YouTubeMediaProvider initialized with specialized YoutubeDL instances.")

    def close(self) -> None:
        """Encerra e limpa os recursos das instâncias do yt-dlp."""
        try:
            if hasattr(self, "_search_ydl"):
                self._search_ydl.close()
            if hasattr(self, "_extractor_ydl"):
                self._extractor_ydl.close()
            logger.debug("YouTubeMediaProvider closed cleanly.")
        except Exception as e:
            logger.warning(f"Error closing YoutubeDL instances: {e}")

    def search(self, query: str, limit: int = 15) -> list[Song]:
        """Search for songs on YouTube using the lightweight search instance."""
        logger.info(f"Searching for '{query}' (limit={limit})")
        search_query = f"ytsearch{limit}:{query}"

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
            logger.error("Unexpected YouTube search error for query '%s': %s", query, e, exc_info=True)
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
                    logger.debug("Audio URL extracted successfully (attempt %d).", attempt)
                    return url

                logger.warning(
                    "yt-dlp returned no URL for '%s' (info was %s) on attempt %d.",
                    video_url,
                    "None" if info is None else "present but missing 'url' key",
                    attempt,
                )

            except yt_dlp.utils.DownloadError as e:
                last_exception = e
                logger.warning("yt-dlp DownloadError on attempt %d/%d: %s", attempt, MAX_RETRIES, e)
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * attempt
                    logger.debug("Retrying audio URL extraction in %.1fs...", delay)
                    time.sleep(delay)
            except Exception as e:
                logger.error("Non-retriable error extracting audio URL for '%s': %s", video_url, e, exc_info=True)
                return None

        logger.error(
            "Failed to extract audio URL for '%s' after %d attempts.",
            video_url,
            MAX_RETRIES,
            exc_info=last_exception is not None,
        )
        return None
