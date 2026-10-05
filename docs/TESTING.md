# InternPilot — Testing Strategy

**Version:** 0.1.0  
**Last Updated:** 2026-10-05  
**Phase:** 0 — Foundation  

---

## Test Organization

```
tests/
├── unit/                  # Isolated component tests
│   ├── test_eligibility.py
│   ├── test_matching.py
│   ├── test_normalization.py
│   ├── test_parsing.py
│   └── test_memory.py
├── integration/           # Cross-component tests
│   ├── test_agent_tools.py
│   ├── test_agent_database.py
│   ├── test_connector_sqlite.py
│   ├── test_connector_file.py
│   └── test_connector_api.py
└── agent/                 # Agent behavior tests
    ├── test_tool_selection.py
    ├── test_clarification.py
    ├── test_error_handling.py
    └── test_safety.py
```

---

## Test Categories

### 1. Unit Tests
Test isolated, deterministic logic.

| What | Examples |
|------|---------|
| Eligibility rules | CGPA thresholds, graduation year checks |
| Parsing | Resume text extraction, opportunity normalization |
| Matching | Score calculations, formula correctness |
| Deadline calculations | Risk assessment, expiry detection |
| Memory operations | Store/retrieve/update preferences |

### 2. Integration Tests
Test cross-component interactions.

| What | Examples |
|------|---------|
| Agent → Tool | Agent calls tool, receives response |
| Agent → Database | Agent reads/writes via repository |
| Connector → SQLite | Query execution, error handling |
| Connector → File | File read, type validation |
| Connector → API | API call, response parsing |

### 3. Agent Behavior Tests
Test that agents make correct decisions.

| What | Examples |
|------|---------|
| Correct tool selection | Agent picks right tool for task |
| Incorrect parameters | Agent handles validation errors |
| Missing information | Agent asks for clarification |
| Ambiguous requests | Agent seeks disambiguation |
| Failed tools | Agent handles gracefully |
| Invalid data | Agent reports rather than fabricates |

### 4. Safety Tests
Test security and governance.

| What | Examples |
|------|---------|
| Unauthorized submission | Blocked without approval |
| Missing approval | Action does not proceed |
| Expired approval | Action does not proceed |
| Malformed input | Validated and rejected |
| Prompt injection | External content sanitized |
| Unauthorized tool access | Rejected by permission check |

---

## Tools

- **pytest** — Test runner
- **pytest-asyncio** — Async test support
- **pytest-cov** — Coverage reports
- **httpx** — API testing (FastAPI TestClient)

---

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage
pytest --cov=backend tests/

# Specific test file
pytest tests/unit/test_eligibility.py -v
```

---

## Definition of Adequate Testing

A feature is adequately tested when:
- [ ] Happy path covered
- [ ] Edge cases identified and tested
- [ ] Error conditions tested
- [ ] No fabricated test data pretending to be real results
- [ ] Tests actually run and pass (verified, not assumed)
