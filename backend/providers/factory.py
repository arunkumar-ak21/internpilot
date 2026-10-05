"""Factory for instantiating opportunity providers based on configuration."""

from backend.core.config import get_settings
from backend.providers.base import OpportunityProvider
from backend.providers.mock import MockOpportunityProvider
from backend.providers.adzuna import AdzunaProvider


def get_provider(provider_name: str | None = None) -> OpportunityProvider:
    """
    Get an instance of the requested opportunity provider.
    If no name is provided, uses the one from application settings.
    """
    settings = get_settings()
    name = provider_name or settings.opportunity_provider

    if name.lower() == "adzuna":
        return AdzunaProvider()
    elif name.lower() == "mock":
        return MockOpportunityProvider()
    else:
        # Default fallback to mock to prevent crashes, but could also raise ValueError
        return MockOpportunityProvider()
