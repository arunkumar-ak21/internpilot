"""Discovery Agent — Fetches internships from configured providers based on candidate skills."""

from __future__ import annotations
import asyncio
from backend.providers.factory import get_provider, get_composite_provider
from backend.providers.base import SearchCriteria


async def run_discovery(skills: list[str], inferred_roles: list[str], location: str | None = None, max_results: int = 15) -> dict:
    """
    Execute discovery search using candidate skills and inferred roles.
    Returns a dict with 'opportunities' list and 'trace' log.
    """
    trace_entries = []

    # Build search queries from skills and roles
    queries = []

    # Query 1: Top skills + internship
    if skills:
        top_skills = " ".join(skills[:4])
        queries.append(f"{top_skills} internship")

    # Query 2: Each inferred role
    for role in inferred_roles[:3]:
        queries.append(role)

    if not queries:
        queries = ["software engineering internship"]

    trace_entries.append(f"Discovery Agent: Generated {len(queries)} search queries from candidate profile.")
    trace_entries.append(f"Discovery Agent: Queries = {queries}")

    provider = get_composite_provider()
    all_opportunities = []
    seen_ids = set()

    for query in queries:
        criteria = SearchCriteria(query=query, location=location, max_results=max_results)
        try:
            result = await asyncio.wait_for(provider.search(criteria), timeout=30.0)
            trace_entries.append(f"Discovery Agent: Query '{query}' returned {len(result.results)} results (status: {result.status}).")
            for outcome in result.provider_outcomes:
                trace_entries.append(f"  Provider {outcome.provider_name}: {outcome.result_count} results, status={outcome.status}" +
                                     (f", error={outcome.error}" if outcome.error else ""))

            for opp in result.results:
                key = opp.source_id or f"{opp.company}:{opp.role}"
                if key not in seen_ids:
                    seen_ids.add(key)
                    all_opportunities.append({
                        "source": opp.source,
                        "source_id": opp.source_id,
                        "company": opp.company,
                        "role": opp.role,
                        "location": opp.location,
                        "description": opp.description,
                        "application_url": opp.application_url,
                    })
        except Exception as e:
            trace_entries.append(f"Discovery Agent: Query '{query}' failed: {e}")

    trace_entries.append(f"Discovery Agent: Total unique opportunities discovered = {len(all_opportunities)}.")

    return {
        "opportunities": all_opportunities[:max_results],
        "trace": trace_entries,
    }
