# ADR-001: LangGraph for Agent Orchestration

**Status:** Accepted  
**Date:** 2026-10-05  
**Decision Makers:** Project Team  

---

## Context

InternPilot requires an orchestration layer that can:
1. Manage stateful, multi-step workflows
2. Support conditional routing (e.g., skip eligibility if data is missing)
3. Allow agents to make decisions about next steps
4. Persist state across workflow stages
5. Support future extension to parallel multi-agent execution
6. Provide checkpointing for long-running workflows

## Decision

Use **LangGraph** as the primary agent orchestration framework.

## Rationale

| Criterion | LangGraph | Plain LangChain | Custom Code |
|-----------|-----------|-----------------|-------------|
| Stateful workflows | ✅ Built-in | ❌ Manual | ❌ Manual |
| Conditional routing | ✅ Graph edges | ⚠️ Limited | ✅ Manual |
| Checkpointing | ✅ Built-in | ❌ No | ❌ Manual |
| Multi-agent support | ✅ Sub-graphs | ⚠️ Limited | ✅ Manual |
| Observability | ✅ Trace events | ⚠️ Basic | ❌ Manual |
| Learning curve | Moderate | Low | N/A |

LangGraph provides the right balance of structure and flexibility for
an agentic system that needs to evolve from a single coordinator to a
multi-agent graph.

## Consequences

- Agents are defined as graph nodes
- State flows through typed state objects
- Conditional edges handle routing logic
- LangChain is still used for model/tool building blocks
- Team must learn LangGraph patterns

## Alternatives Considered

1. **Plain LangChain agents** — Insufficient state management for multi-step workflows
2. **Custom orchestration** — Too much boilerplate, reinventing the wheel
3. **CrewAI** — More opinionated, less control over state and routing
4. **AutoGen** — More focused on conversation patterns, less on structured workflows
