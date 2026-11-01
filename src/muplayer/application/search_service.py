import logging

import diskcache

from muplayer.application.ports import SearchPort
from muplayer.domain import Song

logger = logging.getLogger(__name__)


class SearchService:
    """Orchestrates audio track searches and search result cache management."""

    def __init__(self, search_port: SearchPort, cache: diskcache.Cache | None = None) -> None:
        self.search_port = search_port
        self.cache = cache

    def search(self, query: str, limit: int = 20) -> list[Song]:
        """Searches for tracks after checking the cache."""
        cache_key = f"yt:search:{query}:{limit}"

        if self.cache is not None:
            cached_results = self.cache.get(cache_key)
            if cached_results is not None:
                logger.debug("Cache hit for search query: '%s' (%d results).", query, len(cached_results))
                return cached_results
            logger.debug("Cache miss for search query: '%s'.", query)

        results = self.search_port.search(query, limit=limit)
        logger.debug("Search provider returned %d result(s) for query: '%s'.", len(results), query)

        if results and self.cache is not None:
            self.cache.set(cache_key, results, expire=300)  # 5-minute TTL

        return results
