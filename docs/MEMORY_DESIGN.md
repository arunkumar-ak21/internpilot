# InternPilot — Memory Design

**Version:** 0.1.0  
**Last Updated:** 2026-10-05  
**Phase:** 0 — Foundation  

---

## Overview

InternPilot requires two distinct memory concepts that must not be
conflated with one another or with raw conversation history.

---

## 1. Session State (Short-Term)

Temporary state for the current workflow/conversation. Exists only
for the duration of a user session or workflow execution.

### What It Stores
- Current user request / intent
- Current search criteria
- Current candidate opportunities being evaluated
- Current workflow stage (discovery → eligibility → matching → ...)
- Current approval requests
- Intermediate agent outputs
- Trace ID for the current workflow

### Lifecycle
- Created when a new user session or workflow begins
- Updated as agents process through stages
- Discarded or archived when the session ends

### Implementation Direction
- LangGraph state management (built into the graph checkpointer)
- In-memory during execution, with optional checkpoint persistence

---

## 2. Persistent Memory (Long-Term)

Structured information that should survive across sessions and be
available for future interactions.

### What It Stores
- Preferred roles (e.g., "AI/ML", "Data Science")
- Preferred locations (e.g., "Bangalore", "Remote")
- Minimum stipend threshold
- Career interests and goals
- Previously seen opportunities (to avoid re-showing)
- Previously rejected opportunities (to learn preferences)
- Previously submitted applications
- Profile preferences history
- Any user-corrected information

### Lifecycle
- Created when the user first provides preferences
- Updated when preferences change or new interactions reveal patterns
- Persists indefinitely in the database

### Implementation Direction
- SQLite database via the `CandidatePreference` model
- Repository pattern for clean data access
- Agent retrieves relevant preferences before formulating searches

---

## 3. What Memory Is NOT

| Not Memory | Actual Concept |
|-----------|----------------|
| Raw conversation history | Chat log (UI concern) |
| LLM context window | Prompt engineering (model concern) |
| Cached API responses | Caching layer (infra concern) |
| Computed match scores | Derived data (query concern) |

---

## 4. Retrieval Pattern

```
User says: "Find internships for me"
       |
       v
Agent checks: Do we have persistent preferences?
       |
       +-- YES → Use stored preferences as search defaults
       |         (but allow user to override in this session)
       |
       +-- NO  → Ask user for preferences
                  → Store for future sessions
```

---

## 5. Memory vs State Decision Table

| Data | Type | Reason |
|------|------|--------|
| "User wants AI internships" | Session State | Current request only |
| "User prefers Bangalore" | Persistent Memory | Reusable across sessions |
| "Searching with query: AI ML Bangalore" | Session State | Current execution |
| "User minimum stipend: 15000" | Persistent Memory | Stable preference |
| "3 opportunities found" | Session State | Current results |
| "User rejected Company X last time" | Persistent Memory | Learning |
| "Waiting for approval on Application Y" | Persistent Memory | Cross-session tracking |

---

## Implementation Status

| Component | Phase | Status |
|-----------|-------|--------|
| Session state via LangGraph | Lab 1 (Phase 2) | ✅ Complete |
| Persistent preferences in SQLite | Lab 4 (Phase 7) | ✅ Complete |
| Preference retrieval before search | Lab 4 (Phase 7) | ✅ Complete |
| Cross-session continuity demo | Lab 4 (Phase 7) | ✅ Complete |
