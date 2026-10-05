# InternPilot — Connector Design (MCP-Style)

**Version:** 0.1.0  
**Last Updated:** 2026-10-05  
**Phase:** 0 — Foundation  

---

## Overview

The connector layer provides controlled, auditable access to external
systems. Instead of agents directly coupling to files, databases, and
APIs, all access flows through a unified connector boundary.

This is modeled after the Model Context Protocol (MCP) pattern but
implemented as an internal abstraction initially, with a path toward
full MCP compliance in future labs.

---

## Architecture

```
Agent
  |
  v
Connector Interface
  |
  +-- FileConnector          → Local file system
  +-- DatabaseConnector      → SQLite (PostgreSQL-ready)
  +-- APIConnector           → External opportunity APIs
```

---

## Connector Contract

Every connector implements:

| Method | Description |
|--------|-------------|
| `list_resources()` | List available resources/capabilities |
| `read(resource_id, params)` | Read a resource |
| `write(resource_id, data)` | Write/update a resource |
| `execute(action, params)` | Perform an action |

Plus:

| Concern | Implementation |
|---------|---------------|
| **Access Control** | Each connector defines allowed operations |
| **Audit Logging** | Every connector call is logged with trace ID |
| **Error Handling** | Standardized error responses |
| **Validation** | Input validation before execution |

---

## 1. FileConnector

Provides controlled access to the local file system.

### Capabilities
- Read resume files (PDF, DOCX, TXT)
- List uploaded files
- Read extracted text files
- Write processed outputs

### Security Boundaries
- Restricted to allowed directories (e.g., `data/uploads/`)
- No access to system files or backend source code
- File type validation enforced

---

## 2. DatabaseConnector

Provides controlled access to the SQLite database.

### Capabilities
- Query student profiles
- Query opportunities
- Query applications
- Insert/update records
- Execute predefined queries

### Security Boundaries
- Read-only access for most agent operations
- Write access only through approved repository methods
- No direct SQL execution from agents (repository pattern enforced)

---

## 3. APIConnector

Provides controlled access to external APIs (opportunity providers).

### Capabilities
- Search for opportunities
- Fetch opportunity details
- Rate limiting and retry logic

### Security Boundaries
- API keys managed by the connector, never exposed to agents
- Request rate limiting
- Response validation

---

## Implementation Status

| Connector | Lab | Status |
|-----------|-----|--------|
| FileConnector | Lab 5 (Phase 8) | ✅ Complete |
| DatabaseConnector | Lab 5 (Phase 8) | ✅ Complete |
| APIConnector | Lab 5 (Phase 8) | ✅ Complete |
| Unified connector interface | Lab 5 (Phase 8) | ✅ Complete |
