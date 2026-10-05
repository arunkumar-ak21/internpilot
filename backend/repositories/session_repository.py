"""SQLite persistence for Lab 1 session state and audit records."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import aiosqlite

from backend.agents.coordinator import ConversationState, deserialize_state, serialize_state
from backend.core.database import sqlite_path


class SessionRepository:
    def __init__(self, database_url: str):
        self.database_path = sqlite_path(database_url)

    async def get(self, session_id: str) -> ConversationState | None:
        async with aiosqlite.connect(self.database_path) as connection:
            async with connection.execute("SELECT state_json FROM sessions WHERE session_id = ?", (session_id,)) as cursor:
                row = await cursor.fetchone()
        return deserialize_state(json.loads(row[0])) if row else None

    async def save(self, state: ConversationState) -> None:
        payload = json.dumps(serialize_state(state))
        now = datetime.now(UTC).isoformat()
        async with aiosqlite.connect(self.database_path) as connection:
            await connection.execute("INSERT OR REPLACE INTO sessions (session_id, state_json, updated_at) VALUES (?, ?, ?)", (state.session_id, payload, now))
            await connection.commit()

    async def audit(self, trace_id: str, action: str, details: dict) -> None:
        async with aiosqlite.connect(self.database_path) as connection:
            await connection.execute(
                "INSERT INTO audit_events (event_id, trace_id, action, details_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), trace_id, action, json.dumps(details), datetime.now(UTC).isoformat()),
            )
            await connection.commit()
