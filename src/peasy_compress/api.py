"""peasy-compress API client — Access Peasy Compress tools via REST API.

Usage::

    from peasy_compress.api import PeasyCompressAPI

    api = PeasyCompressAPI()
    tools = api.list_tools()          # paginated: {"count", "next", "results": [...]}
    tool = api.get_tool("zip-compress")
"""

from __future__ import annotations

from typing import Any


class PeasyCompressAPI:
    """REST API client for peasycompress.com.

    All list methods return DRF-paginated responses::

        {"count": 15, "next": "...?page=2", "previous": null, "results": [...]}

    Use ``page`` and ``limit`` to paginate through results.
    """

    def __init__(self, base_url: str = "https://peasycompress.com") -> None:
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        import httpx

        url = f"{self.base_url}{path}"
        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()

    # ── Tools ──────────────────────────────────────────────

    def list_tools(
        self,
        *,
        page: int = 1,
        limit: int = 50,
        category: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List tools (paginated). Filter by category slug or search query."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        return self._get("/api/v1/tools/", params=params)  # type: ignore[no-any-return]

    def get_tool(self, slug: str) -> dict[str, Any]:
        """Get a specific tool by slug."""
        return self._get(f"/api/v1/tools/{slug}/")  # type: ignore[no-any-return]

    # ── Categories ─────────────────────────────────────────

    def list_categories(self, *, page: int = 1, limit: int = 50) -> dict[str, Any]:
        """List tool categories (paginated)."""
        return self._get("/api/v1/categories/", params={"page": page, "limit": limit})  # type: ignore[no-any-return]

    # ── Formats ────────────────────────────────────────────

    def list_formats(
        self,
        *,
        page: int = 1,
        limit: int = 50,
        category: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List file formats (paginated). Filter by category or search query."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        return self._get("/api/v1/formats/", params=params)  # type: ignore[no-any-return]

    def get_format(self, slug: str) -> dict[str, Any]:
        """Get a file format by slug."""
        return self._get(f"/api/v1/formats/{slug}/")  # type: ignore[no-any-return]

    # ── Conversions ────────────────────────────────────────

    def list_conversions(
        self,
        *,
        page: int = 1,
        limit: int = 50,
        source: str | None = None,
        target: str | None = None,
    ) -> dict[str, Any]:
        """List format conversions (paginated). Filter by source/target extension."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if source:
            params["source"] = source
        if target:
            params["target"] = target
        return self._get("/api/v1/conversions/", params=params)  # type: ignore[no-any-return]

    # ── Glossary ───────────────────────────────────────────

    def list_glossary(
        self,
        *,
        page: int = 1,
        limit: int = 50,
        category: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List glossary terms (paginated). Filter by category or search query."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        return self._get("/api/v1/glossary/", params=params)  # type: ignore[no-any-return]

    def get_glossary_term(self, slug: str) -> dict[str, Any]:
        """Get a glossary term by slug."""
        return self._get(f"/api/v1/glossary/{slug}/")  # type: ignore[no-any-return]

    # ── Guides ─────────────────────────────────────────────

    def list_guides(
        self,
        *,
        page: int = 1,
        limit: int = 50,
        category: str | None = None,
        audience_level: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List guides (paginated). Filter by category, audience level, or search query."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if category:
            params["category"] = category
        if audience_level:
            params["audience_level"] = audience_level
        if search:
            params["search"] = search
        return self._get("/api/v1/guides/", params=params)  # type: ignore[no-any-return]

    def get_guide(self, slug: str) -> dict[str, Any]:
        """Get a guide by slug."""
        return self._get(f"/api/v1/guides/{slug}/")  # type: ignore[no-any-return]

    # ── Use Cases ──────────────────────────────────────────

    def list_use_cases(
        self,
        *,
        page: int = 1,
        limit: int = 50,
        industry: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """List use cases (paginated). Filter by industry or search query."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if industry:
            params["industry"] = industry
        if search:
            params["search"] = search
        return self._get("/api/v1/use-cases/", params=params)  # type: ignore[no-any-return]

    # ── Search ─────────────────────────────────────────────

    def search(self, query: str, *, limit: int = 20) -> dict[str, Any]:
        """Search across tools, formats, and glossary."""
        return self._get("/api/v1/search/", params={"q": query, "limit": limit})  # type: ignore[no-any-return]

    # ── Sites ──────────────────────────────────────────────

    def list_sites(self) -> dict[str, Any]:
        """List all 16 Peasy sites."""
        return self._get("/api/v1/sites/")  # type: ignore[no-any-return]

    # ── OpenAPI ────────────────────────────────────────────

    def openapi_spec(self) -> dict[str, Any]:
        """Get the OpenAPI 3.0.3 specification (auto-generated by drf-spectacular)."""
        return self._get("/api/openapi.json")  # type: ignore[no-any-return]
