"""API Connector for external opportunity provider access."""

from typing import Any, Dict, List, Optional

from backend.connectors.base import Connector, Resource
from backend.providers.factory import get_provider
from backend.providers.base import SearchCriteria


class APIConnector(Connector):
    """Provides controlled access to configured external API providers."""

    def __init__(self):
        # Defers to the factory and settings
        self.provider = get_provider()

    def get_name(self) -> str:
        return "OpportunityAPIConnector"

    async def list_resources(self) -> List[Resource]:
        """List the capability of the current provider."""
        return [
            Resource(
                id="opportunity_search",
                name="Opportunity Search API",
                description="Search for internship opportunities externally.",
                type="api"
            )
        ]

    async def read(self, resource_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Reading an API is treated as a search operation."""
        if resource_id != "opportunity_search":
            raise ValueError(f"Unknown API resource: {resource_id}")
            
        params = params or {}
        query = params.get("query")
        if not query:
            raise ValueError("API read requires a 'query' parameter.")
            
        criteria = SearchCriteria(
            query=query,
            location=params.get("location"),
            max_results=params.get("max_results", 10)
        )
        
        results = await self.provider.search(criteria)
        return [res.__dict__ for res in results]

    async def write(self, resource_id: str, data: Any) -> Any:
        """Our external API integrations are currently read-only."""
        raise PermissionError("Opportunity API integrations are read-only.")

    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute specific external API actions (future expansion)."""
        raise NotImplementedError("API actions (e.g. apply) are not yet supported.")
