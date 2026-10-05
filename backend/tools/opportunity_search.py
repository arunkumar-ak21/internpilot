"""Validated tool wrapper around the configured opportunity provider."""

from backend.providers.base import SearchCriteria
from backend.providers.mock import MockOpportunityProvider


async def search_opportunities(query: str, location: str | None, max_results: int = 10) -> list[dict]:
    if not query.strip():
        raise ValueError("Search query must not be empty")
    if not 1 <= max_results <= 20:
        raise ValueError("max_results must be between 1 and 20")
    results = await MockOpportunityProvider().search(SearchCriteria(query=query, location=location, max_results=max_results))
    return [result.__dict__ for result in results]
