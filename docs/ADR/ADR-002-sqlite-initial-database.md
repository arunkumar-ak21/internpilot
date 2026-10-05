# ADR-002: SQLite as Initial Database

**Status:** Accepted  
**Date:** 2026-10-05  
**Decision Makers:** Project Team  

---

## Context

InternPilot needs persistent storage for student profiles, opportunities,
applications, audit events, and preferences. The project starts as a
single-user development system.

## Decision

Use **SQLite** as the initial database, accessed through a **repository
pattern** that abstracts the database engine.

## Rationale

1. **Zero configuration** — No server to install or manage
2. **File-based** — Easy to backup, reset, and distribute
3. **JSON support** — Native JSON functions for semi-structured data
4. **Sufficient for development** — Single-user, low-volume workload
5. **Python built-in** — `sqlite3` module included in standard library

## Migration Strategy

The repository pattern ensures that all database access goes through
interface methods like `get_student(id)`, `save_opportunity(opp)`, etc.

To migrate to PostgreSQL:
1. Update the connection string
2. Adjust JSON field types if needed
3. Run schema migration scripts
4. No business logic changes required

## Consequences

- No concurrent write support (single writer at a time)
- No network access (local only)
- Must design repository interfaces cleanly from the start
- Must avoid SQLite-specific SQL in repository implementations

## Alternatives Considered

1. **PostgreSQL from the start** — Unnecessary complexity for development
2. **MongoDB** — Schema flexibility not needed, relational model fits better
3. **In-memory only** — No persistence across restarts
