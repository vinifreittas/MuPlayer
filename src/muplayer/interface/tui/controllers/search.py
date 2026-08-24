from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Any

from textual import on, work
from textual.css.query import NoMatches
from textual.message_pump import MessagePump

from muplayer.infrastructure.i18n import t
from muplayer.interface.tui.widgets import Header, SearchView

if TYPE_CHECKING:
    from muplayer.application.search_service import SearchService
    from muplayer.infrastructure.config import ConfigManager

logger = logging.getLogger(__name__)


class SearchMixin(MessagePump):
    """Mixin responsible for search execution and search results handling."""

    search_service: SearchService
    config_manager: ConfigManager
    active_view: str

    @on(Header.SearchSubmitted)
    def _handle_search(self, event: Header.SearchSubmitted) -> None:
        self._execute_search_worker(event.query)

    @work(thread=True, exclusive=True)
    def _execute_search_worker(self, query: str) -> None:
        self.call_from_thread(self._set_loading, True)
        try:
            limit = self.config_manager.config.search_limit
            results = self.search_service.search(query, limit=limit)
            self.call_from_thread(self._apply_search_results, query, results)
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            self.call_from_thread(self._set_loading, False)
            self.call_from_thread(self.notify, t("search_network_error", query=query), severity="error")

    def _set_loading(self, is_loading: bool) -> None:
        with contextlib.suppress(Exception):
            self.query_one(SearchView).loading = is_loading

    def _apply_search_results(self, query: str, results: list[Any]) -> None:
        self._set_loading(False)
        with contextlib.suppress(NoMatches):
            self.query_one(SearchView).search_results = results

        self.active_view = "search-view"

        if not results:
            self.notify(t("search_no_results", query=query), severity="warning")
