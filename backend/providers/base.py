"""Provider boundary for opportunity acquisition with rich internship metadata."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any


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
    stipend: str = "₹35,000 / month"
    stipend_numeric: int = 35000
    role_category: str = "Software Engineering"
    work_mode: str = "hybrid"
    duration: str = "3 - 6 Months"
    required_skills: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderOutcomeResult:
    provider_name: str
    attempted: bool
    result_count: int
    status: str
    error: str | None = None


@dataclass
class SearchResult:
    status: str  # success, no_results, partial_success, search_failed
    results: list[RawOpportunity]
    provider_outcomes: list[ProviderOutcomeResult]
    errors: list[str]

    def __len__(self) -> int:
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, idx):
        return self.results[idx]


class OpportunityProvider(ABC):
    @abstractmethod
    async def search(self, criteria: SearchCriteria) -> list[RawOpportunity]:
        """Return source-labelled opportunities."""