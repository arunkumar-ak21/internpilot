# InternPilot — Lab Progress

**Last Updated:** 2026-10-05

---

## Overall Progress

| Phase | Description | Status | Started | Completed |
|-------|-------------|--------|---------|-----------|
| 0 | Repository + Architecture + Contracts | ✅ Complete | 2026-10-05 | 2026-10-05 |
| 1 | Backend / Frontend Skeleton | ✅ Complete | 2026-10-05 | 2026-10-05 |
| 2 | Lab 1 — Agent vs Chatbot | ✅ Complete | 2026-10-05 | 2026-10-05 |
| 3 | Lab 2 — Tool-Using Agent | ✅ Complete | 2026-10-05 | 2026-10-05 |
| 4 | Resume Ingestion | ✅ Complete | 2026-10-05 | 2026-10-05 |
| 5 | Opportunity Provider Abstraction | ⬜ Not Started | — | — |
| 6 | Lab 3 — Internship Research Skill | ⬜ Not Started | — | — |
| 7 | Lab 4 — Memory & Retrieval | ⬜ Not Started | — | — |
| 8 | Lab 5 — MCP-Style Connector | ⬜ Not Started | — | — |
| 9 | End-to-End Lab 1–5 Demo | ⬜ Not Started | — | — |

---

## Phase 0 — Foundation

### Milestone: Repository Setup
- [x] Git repository initialized
- [x] .gitignore created
- [x] .env.example created
- [x] README.md created

### Milestone: Architecture Documentation
- [x] ARCHITECTURE.md created
- [x] DATA_MODEL.md created
- [x] AGENT_CONTRACTS.md created
- [x] TOOL_CONTRACTS.md created
- [x] MEMORY_DESIGN.md created
- [x] CONNECTOR_DESIGN.md created
- [x] SECURITY.md created
- [x] TESTING.md created

### Milestone: Architecture Decision Records
- [x] ADR-001: Why LangGraph for orchestration
- [x] ADR-002: Why SQLite initially
- [x] ADR-003: Why provider abstraction
- [x] ADR-004: Why deterministic eligibility
- [x] ADR-005: Why human approval gates
- [x] ADR-006: Why MCP-style connectors

### Milestone: Project Structure
- [x] Backend folder structure created
- [x] Frontend folder structure created
- [x] Test folder structure created

### Milestone: Environment Verification
- [x] Python 3.13 available
- [x] Node.js v24.16 available
- [x] npm 11.13 available
- [x] Git 2.54 available
- [x] Ollama 0.35 available
- [ ] Ollama model pulled (deferred to Phase 2)
- [x] Python 3.13 virtual environment created (`backend/.venv-native`)
- [x] Backend dependencies installed
- [x] Frontend dependencies installed

### Milestone: Backend / Frontend Skeleton
- [x] FastAPI application factory and lifecycle added
- [x] SQLite initialization and readiness check added
- [x] Versioned health and readiness endpoints added
- [x] React + TypeScript + Vite frontend scaffold added
- [x] Backend lint and tests pass (4 tests)
- [x] Frontend production build passes

---

## Detailed Lab Notes

### Lab 1 — Agent vs Chatbot
**Goal:** Demonstrate agentic behavior (not just chat)  
**Key Acceptance Criteria:**
- Conversational state exists
- Clarification happens when needed
- User request → structured intent
- Agent determines next action
- Workflow is observable

**Status:** ✅ Complete

**Verified implementation:** SQLite-persisted conversation state, structured
search intent extraction, clarification for missing role/location, conditional
`clarify`/`search` routing, and an audit event for every coordinator decision.

---

### Lab 2 — Tool-Using Agent
**Goal:** Add real tools (calculator, file reader, search)  
**Key Acceptance Criteria:**
- Tools have schemas
- Tool calls are observable
- Arguments validated
- Results returned to agent
- Failures handled
- No fake tool calls

**Status:** ✅ Complete

**Verified implementation:** Safe arithmetic tool, upload-directory constrained
text-resume reader, and validated opportunity search via the mock development
provider. Each endpoint produces an audit event; listings are explicitly marked
as mock rather than presented as real opportunities.

---

### Lab 3 — Skill Creation
**Goal:** Create reusable Internship Research Skill  
**Key Acceptance Criteria:**
- Clear input/output schema
- Reusable implementation
- Evidence/source handling
- Error handling
- Documented contract

**Status:** ⬜ Not Started

---

### Lab 4 — Memory & Retrieval
**Goal:** Session state + persistent preferences  
**Key Acceptance Criteria:**
- Memory actually persisted
- Retrieval demonstrated
- Not solely dependent on chat history
- Data ownership clear
- Retrieval behavior testable

**Status:** ⬜ Not Started

---

### Lab 5 — MCP-Style Connector
**Goal:** Connector layer for file/SQLite/API access  
**Key Acceptance Criteria:**
- File capability available
- SQLite capability available
- API capability available
- Common connector boundary
- Access controlled
- Errors propagate correctly
- Calls logged/auditable

**Status:** ⬜ Not Started
