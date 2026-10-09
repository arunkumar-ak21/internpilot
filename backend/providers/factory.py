"""Factory for instantiating opportunity providers based on configuration."""
import asyncio
from backend.core.config import get_settings
from backend.providers.base import OpportunityProvider, SearchCriteria, RawOpportunity, SearchResult, ProviderOutcomeResult
from backend.providers.mock import MockOpportunityProvider
from backend.providers.adzuna import AdzunaProvider
from backend.providers.tavily_search import TavilyProvider
from typing import List

class CompositeProvider:
    def __init__(self, providers: List[OpportunityProvider]):
        self.providers = [p for p in providers if getattr(p, "_configured", True)]

    async def search(self, criteria: SearchCriteria) -> SearchResult:
        if not self.providers:
            return SearchResult(status="search_failed", results=[], provider_outcomes=[], errors=["No configured providers available."])
        
        provider_outcomes = []
        errors = []
        
        async def fetch_provider(provider: OpportunityProvider):
            outcome = ProviderOutcomeResult(
                provider_name=provider.__class__.__name__,
                attempted=True,
                result_count=0,
                status="failed"
            )
            try:
                # Wrap each provider in a bounded timeout
                results = await asyncio.wait_for(provider.search(criteria), timeout=20.0)
                outcome.result_count = len(results)
                outcome.status = "success" if results else "no_results"
                return outcome, results
            except asyncio.TimeoutError:
                outcome.error = "Timeout"
                return outcome, []
            except Exception as e:
                outcome.error = str(e)
                return outcome, []

        tasks = [fetch_provider(p) for p in self.providers]
        fetched_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        
        for r in fetched_results:
            if isinstance(r, Exception):
                errors.append(f"Unexpected gather error: {r}")
                continue
                
            outcome, results = r
            provider_outcomes.append(outcome)
            if outcome.error:
                errors.append(f"{outcome.provider_name} failed: {outcome.error}")
            if results:
                all_results.extend(results)
                
        # Deduplicate based on application_url or canonical source_id
        seen_keys = set()
        deduplicated = []
        for opp in all_results:
            # Prefer canonical source_id if present
            key = opp.source_id if opp.source_id else (opp.application_url if opp.application_url else f"{opp.company.lower()}:{opp.role.lower()}")
            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(opp)
                
        # Determine overall status
        success_count = sum(1 for o in provider_outcomes if o.status == "success")
        failed_count = sum(1 for o in provider_outcomes if o.status == "failed")
        
        if success_count == len(self.providers):
            status = "success" if deduplicated else "no_results"
        elif success_count > 0:
            status = "partial_success"
        elif failed_count == len(self.providers):
            status = "search_failed"
        else:
            status = "no_results"
                
        return SearchResult(
            status=status,
            results=deduplicated,
            provider_outcomes=provider_outcomes,
            errors=errors
        )

def get_provider(provider_name: str | None = None) -> CompositeProvider:
    """
    Get an instance of the requested opportunity provider.
    If no name is provided, uses the one from application settings.
    """
    settings = get_settings()
    name = provider_name or settings.opportunity_provider

    if name.lower() == "mock":
        return CompositeProvider([MockOpportunityProvider()])
        
    adzuna = AdzunaProvider()
    tavily = TavilyProvider()
    
    return CompositeProvider([adzuna, tavily])
