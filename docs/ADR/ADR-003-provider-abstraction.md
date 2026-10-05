# ADR-003: Provider Abstraction for External Data Sources

**Status:** Accepted  
**Date:** 2026-10-05  
**Decision Makers:** Project Team  

---

## Context

InternPilot needs to search for internship opportunities from external
sources. Multiple API providers exist (Adzuna, JSearch, web search).
No single provider offers complete coverage.

## Decision

Implement an **OpportunityProvider abstract interface** that all external
opportunity sources must implement. Agents interact only with the
abstraction, never with specific providers.

## Pattern

```
OpportunityProvider (Abstract)
    |
    +-- AdzunaProvider
    +-- JSearchProvider
    +-- WebSearchProvider
    +-- MockOpportunityProvider
```

Each provider implements:
- `search(query, filters) -> List[RawOpportunity]`
- `fetch_details(source_id) -> RawOpportunity`

## Rationale

1. **API independence** — Switch providers without changing agent code
2. **Multi-source** — Combine results from multiple providers
3. **Testability** — MockProvider enables testing without API calls
4. **Resilience** — Fallback to alternate provider if one fails
5. **Cost control** — Swap to cheaper/free providers as needed

## Consequences

- Small abstraction overhead
- Must define a common RawOpportunity schema
- Provider-specific features must be mapped to the common interface
- New providers require only implementing the interface

## Alternatives Considered

1. **Hard-coded Adzuna** — Fragile, not extensible, blocked if API changes
2. **Generic HTTP client** — Too low-level, no common schema
