import logging

import diskcache

from muplayer.application.ports import SearchPort
from muplayer.domain import Song

logger = logging.getLogger(__name__)


class SearchService:
    """Orquestra buscas de faixas de áudio e gerenciamento de cache de resultados de busca."""

    def __init__(self, search_api: SearchPort, cache: diskcache.Cache | None = None) -> None:
        self.search_api = search_api
        self.cache = cache

    def search(self, query: str, limit: int = 20) -> list[Song]:
        """Executa busca por faixas com consulta prévia ao cache."""
        cache_key = f"yt:search:{query}:{limit}"

        if self.cache and cache_key in self.cache:
            cached_results = self.cache.get(cache_key)
            if cached_results is not None:
                logger.debug(f"Cache hit for search query: '{query}'")
                return cached_results

        results = self.search_api.search(query, max_results=limit)

        if results and self.cache:
            self.cache.set(cache_key, results, expire=300)  # 5 minutos TTL

        return results

    def extract_audio_url(self, video_url: str) -> str | None:
        """Extrai a URL direta do fluxo de áudio de um vídeo."""
        return self.search_api.extract_audio_url(video_url)
