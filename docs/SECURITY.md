# InternPilot — Security

**Version:** 0.1.0  
**Last Updated:** 2026-10-05  
**Phase:** 0 — Foundation  

---

## Core Security Rules

### 1. Secrets Management
- All secrets stored as environment variables
- `.env` file NEVER committed to version control
- `.env.example` provided with placeholder values
- Backend-only secrets (API keys) NEVER sent to frontend

### 2. Agent Permissions
- Each agent has explicitly defined allowed tools
- Agents cannot access tools outside their contract
- Tool authorization is checked before execution

### 3. Human Approval Gates
- Consequential actions require explicit human approval
- Approval state is persisted in the database
- Expired/missing/rejected approval blocks execution
- No auto-approval mechanism exists

### 4. Input Validation
- All API inputs validated via Pydantic models
- File uploads restricted to allowed types and sizes
- External API responses validated before processing
- Database inputs parameterized (no SQL injection)

### 5. Data Privacy
- Student data stored locally (SQLite)
- Resume files stored in restricted directories
- No student data sent to external services without consent
- Audit trail records what data was accessed and when

### 6. Anti-Hallucination
- External data (internships, companies, URLs) never fabricated
- Missing data reported as UNKNOWN, not guessed
- Confidence scores attached where uncertainty exists

### 7. Prompt Injection Defense
- External content (job descriptions) treated as untrusted data
- External content never directly inserted into system prompts
- Agent prompts use structured input, not raw concatenation

---

## Threat Model (Initial)

| Threat | Mitigation |
|--------|-----------|
| API key exposure | Environment variables, .gitignore |
| Unauthorized submission | Approval gates, permission checks |
| SQL injection | Parameterized queries, repository pattern |
| Fabricated data | Anti-hallucination rules, UNKNOWN status |
| Prompt injection via job descriptions | Input sanitization, structured prompts |
| Unauthorized file access | Restricted directory paths |
| Excessive API costs | Rate limiting, request budgets |
