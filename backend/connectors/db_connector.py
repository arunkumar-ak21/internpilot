"""Database Connector for controlled SQLite access via MCP."""

import json
import aiosqlite
from typing import Any, Dict, List, Optional

from backend.connectors.base import Connector, Resource
from backend.core.database import sqlite_path
from backend.core.config import get_settings


class DatabaseConnector(Connector):
    """Provides controlled access to the SQLite database via predefined queries."""

    def __init__(self, database_url: str | None = None):
        settings = get_settings()
        self.database_path = sqlite_path(database_url or settings.database_url)

    def get_name(self) -> str:
        return "SQLiteConnector"

    async def list_resources(self) -> List[Resource]:
        """List available tables/entities as resources."""
        return [
            Resource(id="sessions", name="Sessions Table", description="User session state and memory", type="table"),
            Resource(id="resumes", name="Resumes Table", description="Uploaded and parsed candidate resumes", type="table"),
            Resource(id="opportunities", name="Opportunities Table", description="Discovered internship opportunities", type="table"),
            Resource(id="opportunity_matches", name="Matches Table", description="Scored and ranked candidate matches", type="table"),
            Resource(id="candidate_preferences", name="Preferences", description="Long-term candidate preferences", type="table"),
            Resource(id="audit_events", name="Audit Log", description="System actions log", type="table"),
            Resource(id="agent_workflows", name="Workflows Table", description="Multi-agent workflow runs", type="table"),
        ]

    async def read(self, resource_id: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Read records from a known resource table with safe filtering."""
        params = params or {}
        limit = int(params.get("limit", 10))

        allowed_resources = {
            "sessions",
            "candidate_preferences",
            "audit_events",
            "resumes",
            "opportunities",
            "opportunity_matches",
            "agent_workflows",
        }

        if resource_id not in allowed_resources:
            raise ValueError(f"Resource '{resource_id}' is not an accessible table.")

        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
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
        """Execute predefined analytical and context-retrieval queries."""
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
                async with db.execute(
                    "SELECT * FROM candidate_preferences WHERE student_id = ?",
                    (student_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

        elif action == "get_latest_resume":
            student_id = params.get("student_id")
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                if student_id:
                    cursor = await db.execute(
                        "SELECT * FROM resumes WHERE student_id = ? ORDER BY created_at DESC LIMIT 1",
                        (student_id,),
                    )
                else:
                    cursor = await db.execute(
                        "SELECT * FROM resumes ORDER BY created_at DESC LIMIT 1"
                    )
                row = await cursor.fetchone()
                if not row:
                    return None
                data = dict(row)
                if data.get("parsed_profile_json"):
                    try:
                        data["parsed_profile"] = json.loads(data["parsed_profile_json"])
                    except Exception:
                        data["parsed_profile"] = {}
                return data

        elif action == "get_session":
            session_id = params.get("session_id")
            if not session_id:
                raise ValueError("get_session requires session_id param")
            async with aiosqlite.connect(self.database_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM sessions WHERE session_id = ? LIMIT 1",
                    (session_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return None
                    data = dict(row)
                    try:
                        data["state"] = json.loads(data["state_json"])
                    except Exception:
                        data["state"] = {}
                    return data

        else:
            raise NotImplementedError(f"Action '{action}' is not supported by DatabaseConnector.")