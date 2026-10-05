"""Database Connector for controlled SQLite access."""

import aiosqlite
import json
from typing import Any, Dict, List, Optional

from backend.connectors.base import Connector, Resource
from backend.core.database import sqlite_path
from backend.core.config import get_settings


class DatabaseConnector(Connector):
    """Provides controlled read access to the SQLite database via predefined queries."""

    def __init__(self, database_url: str | None = None):
        settings = get_settings()
        self.database_path = sqlite_path(database_url or settings.database_url)

    def get_name(self) -> str:
        return "SQLiteConnector"

    async def list_resources(self) -> List[Resource]:
        """List available tables/entities as resources."""
        return [
            Resource(id="sessions", name="Sessions Table", description="User session state", type="table"),
            Resource(id="candidate_preferences", name="Preferences", description="Long-term preferences", type="table"),
            Resource(id="audit_events", name="Audit Log", description="System actions log", type="table"),
        ]

    async def read(self, resource_id: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Read records from a known resource table with safe filtering."""
        params = params or {}
        limit = params.get("limit", 10)
        
        # We explicitly map allowed resources to queries to prevent SQL injection
        allowed_resources = ["sessions", "candidate_preferences", "audit_events"]
        
        if resource_id not in allowed_resources:
            raise ValueError(f"Resource '{resource_id}' is not an accessible table.")
            
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            # Safe because resource_id is strictly validated against allowed_resources
            query = f"SELECT * FROM {resource_id} ORDER BY rowid DESC LIMIT ?"
            async with db.execute(query, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def write(self, resource_id: str, data: Any) -> Any:
        """Write operations are restricted to repositories for data integrity."""
        raise PermissionError(
            "Direct write access via DatabaseConnector is denied. "
            "Use the appropriate Repository classes instead."
        )

    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute predefined analytical queries."""
        params = params or {}
        
        if action == "count_audits":
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute("SELECT COUNT(*) FROM audit_events") as cursor:
                    count = (await cursor.fetchone())[0]
                    return {"count": count}
                    
        elif action == "get_preference":
            student_id = params.get("student_id")
            if not student_id:
                raise ValueError("get_preference requires student_id param")
            
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM candidate_preferences WHERE student_id = ?", (student_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
                    
        else:
            raise NotImplementedError(f"Action '{action}' is not supported by DatabaseConnector.")
