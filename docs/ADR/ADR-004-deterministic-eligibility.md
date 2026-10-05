# ADR-004: Deterministic Eligibility Decisions

**Status:** Accepted  
**Date:** 2026-10-05

## Decision

InternPilot will evaluate explicit, objective requirements (for example CGPA,
graduation year, branch, and deadline) using deterministic application code.
Results are `PASS`, `FAIL`, or `UNKNOWN` when source or profile data is absent.

## Rationale

This keeps eligibility reproducible, testable, and explainable. An LLM may
structure ambiguous job text, but it cannot invent a requirement or override a
computed verdict.
