# InternPilot — Lab Progress

**Last Updated:** 2026-10-05

---

## Overall Progress

| Phase | Description | Status | Started | Completed |
|-------|-------------|--------|---------|-----------|
| 0 | Repository + Architecture + Contracts | 🟡 In Progress | 2026-10-05 | — |
| 1 | Backend / Frontend Skeleton | ⬜ Not Started | — | — |
| 2 | Lab 1 — Agent vs Chatbot | ⬜ Not Started | — | — |
| 3 | Lab 2 — Tool-Using Agent | ⬜ Not Started | — | — |
| 4 | Resume Ingestion | ⬜ Not Started | — | — |
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
- [ ] MEMORY_DESIGN.md
- [ ] CONNECTOR_DESIGN.md
- [ ] SECURITY.md
- [ ] TESTING.md

### Milestone: Architecture Decision Records
- [ ] ADR-001: Why LangGraph for orchestration
- [ ] ADR-002: Why SQLite initially
- [ ] ADR-003: Why provider abstraction
- [ ] ADR-004: Why deterministic eligibility
- [ ] ADR-005: Why human approval gates
- [ ] ADR-006: Why MCP-style connectors

### Milestone: Project Structure
- [ ] Backend folder structure created
- [ ] Frontend folder structure created
- [ ] Test folder structure created

### Milestone: Environment Verification
- [x] Python 3.13 available
- [x] Node.js v24.16 available
- [x] npm 11.13 available
- [x] Git 2.54 available
- [x] Ollama 0.35 available
- [ ] Ollama model pulled
- [ ] Python virtual environment created
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed

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

**Status:** ⬜ Not Started

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

**Status:** ⬜ Not Started

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
