"""Unified Connector Interface for MCP-style interactions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Resource(BaseModel):
    """A resource exposed by a connector."""
    id: str
    name: str
    description: str
    type: str


class Connector(ABC):
    """Base interface for all connectors."""

    @abstractmethod
    def get_name(self) -> str:
        """Name of the connector."""
        pass

    @abstractmethod
    async def list_resources(self) -> List[Resource]:
        """List available resources/capabilities."""
        pass

    @abstractmethod
    async def read(self, resource_id: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Read data from a resource."""
        pass

    @abstractmethod
    async def write(self, resource_id: str, data: Any) -> Any:
        """Write or update data in a resource."""
        pass

    @abstractmethod
    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a specific action/capability."""
        pass
