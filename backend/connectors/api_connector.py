"""MCP-style API Connector for external and composite opportunity provider access."""

from typing import Any, Dict, List, Optional

from backend.connectors.base import Connector, Resource
from backend.providers.factory import get_provider, get_composite_provider
from backend.providers.base import SearchCriteria


class APIConnector(Connector):
    """Provides controlled MCP access to configured external API providers."""

    def __init__(self, provider_name: str | None = None):
        self.provider_name = provider_name
        self.provider = get_provider(provider_name)

    def get_name(self) -> str:
        return "OpportunityAPIConnector"

    async def list_resources(self) -> List[Resource]:
        """List the capabilities exposed by the Opportunity API Connector."""
        return [
            Resource(
                id="opportunity_search",
                name="Opportunity Search API",
                description="Search for internship opportunities via configured providers (Adzuna, Tavily, Curated MCP Pool).",
                type="api",
            ),
            Resource(
                id="composite_discovery",
                name="Multi-Provider MCP Discovery",
                description="Run parallel search queries across all active providers and merge deduplicated internships.",
                type="mcp_tool",
            ),
        ]

    async def read(self, resource_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Reading an API resource performs a structured opportunity search."""
        if resource_id not in {"opportunity_search", "composite_discovery"}:
            raise ValueError(f"Unknown API resource: {resource_id}")

        params = params or {}
        query = params.get("query")
        if not query:
            raise ValueError("API read requires a 'query' parameter.")

        criteria = SearchCriteria(
            query=query,
            location=params.get("location"),
            max_results=int(params.get("max_results", 10)),
        )

        provider = get_composite_provider() if resource_id == "composite_discovery" else self.provider
        results = await provider.search(criteria)
        return [res.to_dict() if hasattr(res, "to_dict") else res.__dict__ for res in results]

    async def write(self, resource_id: str, data: Any) -> Any:
        """Our external API integrations are strictly read-only."""
        raise PermissionError("Opportunity API integrations are read-only.")

    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute advanced MCP API actions such as multi-query parallel discovery."""
        params = params or {}

        if action == "mcp_discover":
            queries: List[str] = params.get("queries") or []
            if not queries and params.get("query"):
                queries = [params["query"]]
            if not queries:
                queries = ["software engineering internship"]

            location = params.get("location")
            max_per_query = int(params.get("max_results", 10))
            provider_name = params.get("provider_name")

            composite = (
                get_provider(provider_name)
                if provider_name
                else get_composite_provider()
            )

            all_opportunities: list[dict] = []
            seen_keys: set[str] = set()
            provider_outcomes: list[dict] = []
            errors: list[str] = []

            for q in queries[:5]:
                criteria = SearchCriteria(query=q, location=location, max_results=max_per_query)
                search_res = await composite.search(criteria)

                if hasattr(search_res, "provider_outcomes"):
                    for o in search_res.provider_outcomes:
                        provider_outcomes.append(o.__dict__)
                if hasattr(search_res, "errors") and search_res.errors:
                    errors.extend(search_res.errors)

                items = search_res.results if hasattr(search_res, "results") else search_res
                for opp in items:
                    opp_dict = opp.to_dict() if hasattr(opp, "to_dict") else dict(opp.__dict__)
                    dedup_key = f"{opp_dict.get('company', '').lower().strip()}::{opp_dict.get('role', '').lower().strip()}"
                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        all_opportunities.append(opp_dict)

            return {
                "status": "success" if all_opportunities else "no_results",
                "opportunities": all_opportunities,
                "provider_outcomes": provider_outcomes,
                "errors": errors,
                "queries_executed": queries[:5],
            }

        raise NotImplementedError(f"API action '{action}' is not yet supported.")