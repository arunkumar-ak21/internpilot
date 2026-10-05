# InternPilot — Architecture Document

**Version:** 0.1.0  
**Last Updated:** 2026-10-05  
**Phase:** 0 — Foundation  

---

## 1. System Overview

InternPilot is an Agentic AI platform that assists students in discovering,
evaluating, applying to, and tracking internship opportunities. The system
uses a combination of LLM-driven reasoning and deterministic business logic,
with a human-in-the-loop for consequential actions.

### Design Principles

1. **Separation of Concerns** — LLM reasoning, deterministic logic, data
   storage, and human authority each have clearly defined responsibilities.
2. **Provider Abstraction** — External data sources (opportunity APIs, LLM
   providers) are accessed through abstract interfaces.
3. **Incremental Evolution** — The architecture grows one verified layer at
   a time. No premature complexity.
4. **Auditability** — Every agent action, tool call, and state change is
   traceable.
5. **Human Authority** — Consequential actions require explicit human approval.

---

## 2. Logical Architecture

```
                    STUDENT
                       |
                       v
                React Frontend            (Presentation Layer)
                       |
                       v
                 FastAPI Backend           (API Layer)
                       |
                       v
              Agentic Orchestrator         (Orchestration Layer)
                 /           \
                /             \
               v               v
         Agent / Graph       Memory        (Agent + State Layer)
               |
      +--------+---------+
      |        |         |
      v        v         v
    Tools    Skills    Connectors          (Capability Layer)
      |        |         |
      +--------+---------+
               |
               v
       External Systems                   (Integration Layer)
       /       |        \
    Files   SQLite      APIs
```

### Layer Responsibilities

| Layer | Responsibility | Examples |
|-------|---------------|----------|
| Presentation | User interaction, display | React components, chat UI |
| API | Request handling, auth, validation | FastAPI routes, Pydantic models |
| Orchestration | Workflow management, routing | LangGraph state machine |
| Agent + State | Reasoning, decisions, memory | Coordinator, Discovery Agent |
| Capability | Deterministic actions, skills | Tools, Research Skill, Connectors |
| Integration | External system access | SQLite, file system, opportunity APIs |

---

## 3. Responsibility Separation

### LLM Responsibilities (Non-Deterministic)
- Natural language understanding & intent interpretation
- Resume information extraction
- Job description interpretation
- Semantic skill matching
- Research synthesis & personalized explanations
- Draft generation for applications
- Clarification & ambiguous reasoning

### Deterministic Logic Responsibilities
- Eligibility rules (CGPA checks, branch, graduation year)
- Date & deadline calculations
- Match score computation (formula-based)
- Authentication & authorization
- Application status transitions
- Approval state management
- Audit record creation

### Database Responsibilities
- Student profiles & preferences
- Resumes (original + parsed)
- Opportunities (raw + normalized)
- Applications & their lifecycle
- Memory (session + persistent)
- Audit events

### Human Responsibilities
- Final application submission approval
- Sensitive information disclosure decisions
- Official evaluation & grading
- Destructive action authorization

---

## 4. Data Flow: Primary Use Case

```
Student Request ("Find AI internships in Bangalore")
       |
       v
   API Layer — validates request, creates session
       |
       v
   Coordinator Agent — interprets intent, checks state
       |
       v
   Profile Check — do we have enough student info?
       |
       +-- NO --> Clarification (ask student for missing info)
       |
       +-- YES --> proceed
       |
       v
   Discovery Agent — formulates search, calls OpportunitySearchTool
       |
       v
   OpportunityProvider (abstraction) — fetches from configured sources
       |
       v
   Raw Results — normalized, deduplicated, stored
       |
       v
   Eligibility Agent — deterministic checks per opportunity
       |
       v
   Match Engine — structured scoring (skill, role, location, preference)
       |
       v
   Research Skill — investigates top-ranked opportunities
       |
       v
   Ranked Results — presented to student with explanations
       |
       v
   Student selects → Application Agent → Human Approval → Action
```

---

## 5. Provider Abstraction Pattern

```
OpportunityProvider (Abstract Interface)
       |
       +-- AdzunaProvider
       +-- JSearchProvider
       +-- WebSearchProvider
       +-- MockOpportunityProvider    (for development & testing)
```

Each provider implements the same interface:
- `search(query, filters) -> List[RawOpportunity]`
- `fetch_details(source_id) -> RawOpportunity`

The agent layer never knows which provider is active.

Similarly for LLM:
```
LLMProvider (Abstract Interface)
       |
       +-- OllamaProvider
       +-- OpenAIProvider
       +-- AnthropicProvider
```

---

## 6. Component Map (Phase 0)

These are the planned components. They will be implemented incrementally.

### Backend (`backend/`)

| Directory | Purpose | Phase |
|-----------|---------|-------|
| `core/` | Config, settings, dependency injection | 1 |
| `models/` | Pydantic schemas, DB models | 1 |
| `api/` | FastAPI routes | 1 |
| `repositories/` | Data access (SQLite) | 1 |
| `services/` | Business logic | 1 |
| `agents/` | Agent definitions, LangGraph orchestration | 2 |
| `tools/` | Agent-callable tools | 3 |
| `skills/` | Reusable capability packages | 6 |
| `connectors/` | MCP-style connector layer | 8 |
| `providers/` | External source abstractions | 5 |

### Frontend (`frontend/`)

| Area | Purpose | Phase |
|------|---------|-------|
| Chat interface | Agent interaction | 2 |
| Profile view | Student profile & preferences | 2 |
| Opportunity explorer | Browse/filter/compare opportunities | 3 |
| Application tracker | Track application lifecycle | Future |
| Agent trace viewer | Observe agent decisions | Future |

---

## 7. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend framework | FastAPI | Async, Pydantic integration, OpenAPI docs |
| Agent orchestration | LangGraph | Stateful graphs, conditional routing, checkpoints |
| Agent building blocks | LangChain | Tool/model abstractions, composability |
| Database | SQLite | Zero setup, file-based, sufficient for dev |
| DB design | Repository pattern | Clean migration path to PostgreSQL |
| LLM (initial) | Ollama (local) | Free, private, no API key needed |
| LLM abstraction | Provider interface | Swap models without code changes |
| Frontend | React + TypeScript | Type safety, ecosystem, reusability |

Detailed rationale is documented in [ADR records](ADR/).

---

## 8. Security Architecture

- **Secrets**: Environment variables only, never hard-coded
- **API keys**: Backend-only, never exposed to frontend
- **Agent permissions**: Each agent has explicitly defined allowed tools
- **Approval gates**: Consequential actions blocked without human approval
- **Input validation**: Pydantic models validate all inputs
- **Audit trail**: All agent actions are logged with trace IDs

---

## 9. Observability

- **Trace IDs**: Every workflow execution gets a unique trace ID
- **Audit events**: Stored in the database with actor, action, tool, I/O refs
- **Agent activity log**: Human-readable trace of agent decisions
- **Error recording**: Failures are captured with context, never silently swallowed

---

## 10. Evolution Path

| Current (Labs 1-5) | Future (Labs 6-14) |
|---------------------|---------------------|
| Single coordinator agent | Multi-agent graph with parallel execution |
| Sequential workflow | Conditional branching, loops |
| Basic tool calling | Deep research workflows |
| Session + persistent memory | Vector search, advanced retrieval |
| MCP-style connectors | Full MCP protocol support |
| SQLite | PostgreSQL migration |
| Local Ollama | Cloud LLM providers |

The architecture is designed so that each future extension is an addition,
not a rewrite.
