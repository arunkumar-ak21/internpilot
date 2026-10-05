"""SQLite persistence for Candidate Preferences (Long-term Memory)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import aiosqlite

from backend.models.schemas import CandidatePreference
from backend.core.database import sqlite_path


class PreferenceRepository:
    def __init__(self, database_url: str):
        self.database_path = sqlite_path(database_url)

    async def get_by_student_id(self, student_id: str) -> CandidatePreference | None:
        """Retrieve a student's long-term preferences."""
        async with aiosqlite.connect(self.database_path) as connection:
            async with connection.execute(
                """
                SELECT id, student_id, target_roles_json, locations_json, work_modes_json, 
                       minimum_stipend, duration_preferences, availability, additional_constraints, updated_at 
                FROM candidate_preferences 
                WHERE student_id = ?
                """, 
                (student_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
        if not row:
            return None
            
        return CandidatePreference(
            id=row[0],
            student_id=row[1],
            target_roles=json.loads(row[2]) if row[2] else None,
            locations=json.loads(row[3]) if row[3] else None,
            work_modes=json.loads(row[4]) if row[4] else None,
            minimum_stipend=row[5],
            duration_preferences=row[6],
            availability=row[7],
            additional_constraints=row[8],
            updated_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(UTC)
        )

    async def save(self, preference: CandidatePreference) -> None:
        """Save or update a student's long-term preferences."""
        now = datetime.now(UTC).isoformat()
        
        async with aiosqlite.connect(self.database_path) as connection:
            # Check if exists first to maintain the UUID if updating
            async with connection.execute("SELECT id FROM candidate_preferences WHERE student_id = ?", (preference.student_id,)) as cursor:
                row = await cursor.fetchone()
                
            if row:
                # Update existing
                await connection.execute(
                    """
                    UPDATE candidate_preferences SET
                        target_roles_json = ?, locations_json = ?, work_modes_json = ?,
                        minimum_stipend = ?, duration_preferences = ?, availability = ?,
                        additional_constraints = ?, updated_at = ?
                    WHERE student_id = ?
                    """,
                    (
                        json.dumps(preference.target_roles) if preference.target_roles else None,
                        json.dumps(preference.locations) if preference.locations else None,
                        json.dumps(preference.work_modes) if preference.work_modes else None,
                        preference.minimum_stipend,
                        preference.duration_preferences,
                        preference.availability,
                        preference.additional_constraints,
                        now,
                        preference.student_id
                    )
                )
            else:
                # Insert new
                await connection.execute(
                    """
                    INSERT INTO candidate_preferences 
                    (id, student_id, target_roles_json, locations_json, work_modes_json, 
                     minimum_stipend, duration_preferences, availability, additional_constraints, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        preference.id,
                        preference.student_id,
                        json.dumps(preference.target_roles) if preference.target_roles else None,
                        json.dumps(preference.locations) if preference.locations else None,
                        json.dumps(preference.work_modes) if preference.work_modes else None,
                        preference.minimum_stipend,
                        preference.duration_preferences,
                        preference.availability,
                        preference.additional_constraints,
                        now
                    )
                )
            await connection.commit()
