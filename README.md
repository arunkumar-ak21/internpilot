# InternPilot

**Agentic Internship Discovery, Application & Tracking Platform**

An Agentic AI platform that helps students discover relevant internship
opportunities, verify eligibility, evaluate personal fit, research opportunities,
prepare applications, track application progress, and eventually track the
internship through final evaluation — all in one auditable record.

---

## Project Status

| Phase | Milestone | Status |
|-------|-----------|--------|
| 0 | Repository + Architecture + Contracts | ✅ Complete |
| 1 | Backend / Frontend skeleton | ✅ Complete |
| 2 | Lab 1 — Agent vs Chatbot | ✅ Complete |
| 3 | Lab 2 — Tool-Using Agent | ✅ Complete |
| 4 | Resume Ingestion | ✅ Complete |
| 5 | Opportunity Provider Abstraction | ✅ Complete |
| 6 | Lab 3 — Internship Research Skill | ✅ Complete |
| 7 | Lab 4 — Memory & Retrieval | ✅ Complete |
| 8 | Lab 5 — MCP-Style Connector | ✅ Complete |
| 9 | End-to-End Lab 1–5 Demo | ✅ Complete |

## Run the foundation

The backend uses the native CPython environment at `backend/.venv-native`.

```powershell
.\backend\.venv-native\Scripts\uvicorn.exe backend.main:app --reload
```

The API health endpoint is `http://localhost:8000/api/v1/health`. Start the
frontend in a second terminal:

```powershell
npm --prefix frontend run dev
```

Run verification with:

```powershell
.\backend\.venv-native\Scripts\ruff.exe check backend tests
.\backend\.venv-native\Scripts\pytest.exe -q
npm --prefix frontend run build
```

---

## Architecture Overview

```
                    STUDENT
                       |
                       v
                React Frontend
                       |
                       v
                 FastAPI Backend
                       |
                       v
              Agentic Orchestrator
                 /           \
                /             \
               v               v
         Agent / Graph       Memory
               |
      +--------+---------+
      |        |         |
      v        v         v
    Tools    Skills    Connectors
      |        |         |
      +--------+---------+
               |
               v
       External Systems
       /       |        \
    Files   SQLite      APIs
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic |
| Agent Orchestration | LangGraph, LangChain |
| LLM | Ollama (local, swappable) |
| Database | SQLite (PostgreSQL-ready design) |
| Search | Provider abstraction pattern |

---

## Project Structure

```
internpilot/
├── backend/               # Python FastAPI backend
│   ├── agents/            # Agent definitions & orchestration
│   ├── api/               # FastAPI routes
│   ├── connectors/        # MCP-style connector layer
│   ├── core/              # Config, dependencies, shared utilities
│   ├── models/            # Pydantic models & DB schemas
│   ├── providers/         # Opportunity provider abstraction
│   ├── repositories/      # Data access layer
│   ├── services/          # Business logic services
│   ├── skills/            # Reusable capability packages
│   └── tools/             # Agent tools
├── frontend/              # React TypeScript frontend
├── data/                  # Local data storage (SQLite, uploads)
├── tests/                 # Test suites
│   ├── unit/
│   ├── integration/
│   └── agent/
└── docs/                  # Architecture & design documentation
    └── ADR/               # Architecture Decision Records
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama (for local LLM)
- Git

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd "Agentic AI"

# 2. Copy environment variables
cp .env.example .env

# 3. Backend setup
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 4. Frontend setup
cd ../frontend
npm install

# 5. Pull an Ollama model
ollama pull llama3.2

# 6. Start development
# Terminal 1: Backend
cd backend && uvicorn main:app --reload
# Terminal 2: Frontend
cd frontend && npm run dev
```

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Agent Contracts](docs/AGENT_CONTRACTS.md)
- [Tool Contracts](docs/TOOL_CONTRACTS.md)
- [Data Model](docs/DATA_MODEL.md)
- [Memory Design](docs/MEMORY_DESIGN.md)
- [Connector Design](docs/CONNECTOR_DESIGN.md)
- [Security](docs/SECURITY.md)
- [Testing](docs/TESTING.md)
- [Lab Progress](docs/LAB_PROGRESS.md)

---

## License

This project is developed for academic coursework (Worklet 10 — Agentic AI).
