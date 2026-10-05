"""SQLite lifecycle management for the initial InternPilot backend."""

from __future__ import annotations

from pathlib import Path

import aiosqlite

from backend.core.config import get_settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resumes (
    resume_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    version INTEGER NOT NULL,
    extracted_text TEXT,
    parsed_profile_json TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS candidate_preferences (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    target_roles_json TEXT,
    locations_json TEXT,
    work_modes_json TEXT,
    minimum_stipend INTEGER,
    duration_preferences TEXT,
    availability TEXT,
    additional_constraints TEXT,
    updated_at TEXT NOT NULL
);
"""


def sqlite_path(database_url: str) -> Path:
    """Return the filesystem path from the supported SQLite URL format."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// database URLs are supported in Phase 1")
    return Path(database_url.removeprefix(prefix))


async def initialize_database() -> None:
    """Create the Phase 1 database and its metadata table if needed."""
    database_path = sqlite_path(get_settings().database_url)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(database_path) as connection:
        await connection.executescript(SCHEMA_SQL)
        await connection.execute(
            "INSERT OR IGNORE INTO schema_metadata (key, value) VALUES (?, ?)",
            ("schema_version", "1"),
        )
        await connection.commit()


async def database_is_ready() -> bool:
    """Check that the initialized database can answer a simple query."""
    database_path = sqlite_path(get_settings().database_url)
    if not database_path.exists():
        return False
    try:
        async with aiosqlite.connect(database_path) as connection:
            async with connection.execute("SELECT 1") as cursor:
                return (await cursor.fetchone()) == (1,)
    except aiosqlite.Error:
        return False
