from typing import List, Dict, Any, Optional

from tavily import TavilyClient

from backend.config import settings
from backend.utils.logger_utils import logger

MAX_INPUT_LENGTH = 500


class WebSearchClient:
    def __init__(self, api_key: Optional[str]):
        self._enabled = bool(api_key and settings.web_enabled)
        self._client = TavilyClient(api_key=api_key) if self._enabled else None

    def _trim_query(self, query: str) -> str:
        if len(query) <= MAX_INPUT_LENGTH:
            return query
        return query[:MAX_INPUT_LENGTH].rsplit(" ", 1)[0]

    def is_enabled(self) -> bool:
        return self._enabled

    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        if settings.is_dev:
            logger.info("Web search: Dev mode")
            return []

        if not self._enabled or not self._client:
            logger.info("Web search: disabled or client not initialized")
            return []

        trimmed = self._trim_query(query)
        if trimmed != query:
            logger.info("Web search: query trimmed from %s to %s chars", len(query), len(trimmed))

        try:
            logger.info("Web search: querying Tavily for '%s'", trimmed)
            result = self._client.search(
                query=trimmed,
                max_results=max_results,
                search_depth="basic",
                include_answer=True,
                include_raw_content=False,
            )

            sources = result.get("results", [])
            logger.info("Web search: got %s results", len(sources))
            return sources
        except Exception as e:
            logger.error("Web search: Tavily query failed: %s", e)
            return []


web_client = WebSearchClient(api_key=settings.web_token)
