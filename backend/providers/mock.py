"""Development provider. Its data is explicitly labelled mock, never real."""

from backend.providers.base import OpportunityProvider, RawOpportunity, SearchCriteria


class MockOpportunityProvider(OpportunityProvider):
    async def search(self, criteria: SearchCriteria) -> list[RawOpportunity]:
        return [
            RawOpportunity(
                source="mock",
                source_id="demo-ai-001",
                company="Example Labs (mock listing)",
                role=f"{criteria.query} Intern",
                location=criteria.location or "Remote",
                description="Development-only mock opportunity. Not a real listing.",
            )
        ][: criteria.max_results]
