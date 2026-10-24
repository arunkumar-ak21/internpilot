"""Validated MCP-aware tool wrapper around the configured opportunity provider."""

from __future__ import annotations

from backend.connectors.api_connector import APIConnector
from backend.providers.base import SearchCriteria
from backend.providers.factory import get_provider


async def search_opportunities(
    query: str,
    location: str | None = None,
    max_results: int = 10,
    provider_name: str | None = None,
) -> list[dict]:
    if not query or not query.strip():
        raise ValueError("Search query must not be empty")
    if not 1 <= max_results <= 25:
        raise ValueError("max_results must be between 1 and 25")

    # If a specific provider is requested (e.g. in unit tests), call it directly
    if provider_name:
        provider = get_provider(provider_name)
        results = await provider.search(
            SearchCriteria(query=query.strip(), location=location, max_results=max_results)
        )
        return [res.to_dict() if hasattr(res, "to_dict") else res.__dict__ for res in results]

    # Route via the MCP APIConnector
    connector = APIConnector()
    return await connector.read(
        "opportunity_search",
        {"query": query.strip(), "location": location, "max_results": max_results},
    )