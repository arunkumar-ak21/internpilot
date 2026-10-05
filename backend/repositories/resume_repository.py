"""SQLite repository for preserved resumes and their derived representations."""

import json

import aiosqlite

from backend.core.database import sqlite_path


class ResumeRepository:
    def __init__(self, database_url: str): self.database_path = sqlite_path(database_url)

    async def save(self, resume: dict) -> None:
        async with aiosqlite.connect(self.database_path) as connection:
            await connection.execute("INSERT INTO resumes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (resume["resume_id"], resume["student_id"], resume["file_name"], resume["file_path"], resume["version"], resume["extracted_text"], json.dumps(resume["parsed_profile"]), resume["created_at"]))
            await connection.commit()
