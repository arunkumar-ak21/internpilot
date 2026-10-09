"""Provider boundary for opportunity acquisition."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchCriteria:
    query: str
    location: str | None = None
    max_results: int = 10


@dataclass(frozen=True)
class RawOpportunity:
    source: str
    source_id: str
    company: str
    role: str
    location: str | None
    description: str
    application_url: str | None = None


@dataclass
class ProviderOutcomeResult:
    provider_name: str
    attempted: bool
    result_count: int
    status: str
    error: str | None = None

@dataclass
class SearchResult:
    status: str # success, no_results, partial_success, search_failed
    results: list[RawOpportunity]
    provider_outcomes: list[ProviderOutcomeResult]
    errors: list[str]


class OpportunityProvider(ABC):
    @abstractmethod
    async def search(self, criteria: SearchCriteria) -> list[RawOpportunity]:
        """Return source-labelled, unnormalized opportunities."""
