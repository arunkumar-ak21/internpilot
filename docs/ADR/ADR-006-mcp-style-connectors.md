# ADR-006: MCP-Style Connector Boundary

**Status:** Accepted  
**Date:** 2026-10-05

## Decision

Files, SQLite, and external APIs will be reached through common controlled
connector interfaces, rather than directly by agents.

## Rationale

The boundary constrains permissions, validates inputs, preserves auditability,
and permits a future migration to a real MCP server without coupling agent
logic to infrastructure details.
