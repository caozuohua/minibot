"""Search API tool with multiple backend support."""

import logging
import os

import requests

from src.tools.base_tool import Tool, ToolResult

logger = logging.getLogger(__name__)


class SearchTool(Tool):
    """Search the web using various search backends."""

    def __init__(self, backend: str = "tavily", api_key: str = ""):
        self.backend = backend
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return (
            "Search the web for information. "
            "Returns relevant search results with titles, snippets, and URLs."
        )

    def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        """Search the web."""
        try:
            if self.backend == "tavily":
                return self._tavily_search(query, max_results)
            elif self.backend == "searxng":
                return self._searxng_search(query, max_results)
            elif self.backend == "google":
                return self._google_search(query, max_results)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown search backend: {self.backend}",
                )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )

    def _tavily_search(self, query: str, max_results: int) -> ToolResult:
        """Search using Tavily API."""
        if not self.api_key:
            return ToolResult(
                success=False, output="", error="Tavily API key not configured"
            )

        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for r in data.get("results", [])[:max_results]:
            results.append(
                f"Title: {r.get('title', 'N/A')}\n"
                f"URL: {r.get('url', 'N/A')}\n"
                f"Snippet: {r.get('content', 'N/A')}\n"
            )

        return ToolResult(
            success=True,
            output="\n---\n".join(results) if results else "No results found.",
        )

    def _searxng_search(self, query: str, max_results: int) -> ToolResult:
        """Search using SearXNG instance."""
        # Default to public instance; configure via base_url for self-hosted
        base_url = "https://searx.be"
        response = requests.get(
            f"{base_url}/search",
            params={"q": query, "format": "json"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for r in data.get("results", [])[:max_results]:
            results.append(
                f"Title: {r.get('title', 'N/A')}\n"
                f"URL: {r.get('url', 'N/A')}\n"
                f"Snippet: {r.get('content', 'N/A')}\n"
            )

        return ToolResult(
            success=True,
            output="\n---\n".join(results) if results else "No results found.",
        )

    def _google_search(self, query: str, max_results: int) -> ToolResult:
        """Search using Google Custom Search API."""
        if not self.api_key:
            return ToolResult(
                success=False, output="", error="Google API key not configured"
            )

        # Requires both API key and CX ID
        cx = os.environ.get("GOOGLE_CX_ID", "")
        if not cx:
            return ToolResult(
                success=False, output="", error="GOOGLE_CX_ID not configured"
            )

        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": self.api_key,
                "cx": cx,
                "q": query,
                "num": max_results,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for r in data.get("items", [])[:max_results]:
            results.append(
                f"Title: {r.get('title', 'N/A')}\n"
                f"URL: {r.get('link', 'N/A')}\n"
                f"Snippet: {r.get('snippet', 'N/A')}\n"
            )

        return ToolResult(
            success=True,
            output="\n---\n".join(results) if results else "No results found.",
        )
