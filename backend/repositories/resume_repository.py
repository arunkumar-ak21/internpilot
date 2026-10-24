"""SQLite repository for preserved resumes and their derived representations."""

from __future__ import annotations

import json
import aiosqlite

from backend.core.database import sqlite_path


class ResumeRepository:
    def __init__(self, database_url: str):
        self.database_path = sqlite_path(database_url)

    def _hydrate_row(self, row: aiosqlite.Row) -> dict:
        """Merge row columns with parsed_profile_json so all callers have full context."""
        parsed = json.loads(row["parsed_profile_json"]) if row["parsed_profile_json"] else {}
        if not isinstance(parsed, dict):
            parsed = {}
        # Ensure top-level keys exist whether caller expects parsed_profile fields or metadata fields
        result = {
            **parsed,
            "resume_id": row["resume_id"],
            "student_id": row["student_id"],
            "file_name": row["file_name"],
            "file_path": row["file_path"],
            "version": row["version"],
            "extracted_text": row["extracted_text"] or "",
            "created_at": row["created_at"],
            "parsed_profile": parsed,
        }
        return result

    async def save(self, resume: dict) -> None:
        async with aiosqlite.connect(self.database_path) as connection:
            await connection.execute(
                "INSERT OR REPLACE INTO resumes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    resume["resume_id"],
                    resume["student_id"],
                    resume["file_name"],
                    resume["file_path"],
                    resume.get("version", 1),
                    resume.get("extracted_text", ""),
                    json.dumps(resume.get("parsed_profile", {})),
                    resume["created_at"],
                ),
            )
            await connection.commit()

    async def get_latest_by_student(self, student_id: str) -> dict | None:
        async with aiosqlite.connect(self.database_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT * FROM resumes WHERE student_id = ? ORDER BY created_at DESC LIMIT 1",
                (student_id,),
            )
            row = await cursor.fetchone()
            if row:
                return self._hydrate_row(row)
            return None

    async def get_by_id(self, resume_id: str) -> dict | None:
        async with aiosqlite.connect(self.database_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT * FROM resumes WHERE resume_id = ? LIMIT 1",
                (resume_id,),
            )
            row = await cursor.fetchone()
            if row:
                return self._hydrate_row(row)
            return None

    async def get_latest(self) -> dict | None:
        """Return the most recently uploaded resume across all sessions/students."""
        async with aiosqlite.connect(self.database_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT * FROM resumes ORDER BY created_at DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            if row:
                return self._hydrate_row(row)
            return None