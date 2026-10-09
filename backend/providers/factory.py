"""Factory for instantiating opportunity providers based on configuration."""

from backend.core.config import get_settings
from backend.providers.base import OpportunityProvider, SearchCriteria, RawOpportunity
from backend.providers.mock import MockOpportunityProvider
from backend.providers.adzuna import AdzunaProvider
from backend.providers.tavily_search import TavilyProvider
from typing import List

class CompositeProvider(OpportunityProvider):
    def __init__(self, providers: List[OpportunityProvider]):
        self.providers = [p for p in providers if getattr(p, "_configured", True)]

    async def search(self, criteria: SearchCriteria) -> List[RawOpportunity]:
        if not self.providers:
            raise ValueError("No configured opportunity providers available.")
        
        all_results = []
        for provider in self.providers:
            try:
                results = await provider.search(criteria)
                all_results.extend(results)
            except Exception as e:
                print(f"[CompositeProvider] Provider {provider.__class__.__name__} failed: {e}")
                continue
        
        # Deduplicate based on application_url or (company, role)
        seen_keys = set()
        deduplicated = []
        for opp in all_results:
            key = opp.application_url if opp.application_url else f"{opp.company.lower()}:{opp.role.lower()}"
            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(opp)
                
        return deduplicated

def get_provider(provider_name: str | None = None) -> OpportunityProvider:
    """
    Get an instance of the requested opportunity provider.
    If no name is provided, uses the one from application settings.
    """
    settings = get_settings()
    name = provider_name or settings.opportunity_provider

    if name.lower() == "mock":
        return MockOpportunityProvider()
        
    adzuna = AdzunaProvider()
    tavily = TavilyProvider()
    
    return CompositeProvider([adzuna, tavily])
