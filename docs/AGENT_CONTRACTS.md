# InternPilot — Agent Contracts

**Version:** 0.1.0  
**Last Updated:** 2026-10-05  
**Phase:** 0 — Foundation  

---

## Overview

Every production agent in InternPilot has a defined contract. An agent
is only valid if it demonstrates genuine agentic behavior: goal
interpretation, decision making, tool selection, state management,
observation, and/or conditional routing.

A component is NOT an agent simply because its class is named `Agent`.

---

## Contract Template

Each agent contract specifies:

| Field | Description |
|-------|-------------|
| **Purpose** | What this agent exists to do |
| **Inputs** | What state/data it receives |
| **Outputs** | What structured result it produces |
| **Tools** | What it is allowed to call |
| **Constraints** | What it must NOT do |
| **Failure Behavior** | What happens when info is missing or a tool fails |
| **Termination Condition** | When the agent should stop |

---

## 1. Coordinator Agent

| Field | Specification |
|-------|---------------|
| **Purpose** | Understand the student's high-level goal, manage the overall workflow, initialize state, route tasks to specialized agents, handle exceptions, and determine the next stage. |
| **Inputs** | User message, session state, student profile (if exists), current workflow stage |
| **Outputs** | Updated session state, routing decision, response to user, or delegation to specialist agent |
| **Tools** | `get_candidate_profile`, `get_preferences`, `create_audit_event` |
| **Constraints** | Must NOT directly perform specialized operations (search, eligibility, research). Must NOT fabricate data. Must NOT skip clarification when critical info is missing. |
| **Failure Behavior** | If profile is incomplete → ask user for clarification. If a specialist agent fails → record error, inform user, suggest alternatives. |
| **Termination Condition** | When the user's current request has been fully addressed or delegated. |

---

## 2. Opportunity Discovery Agent

| Field | Specification |
|-------|---------------|
| **Purpose** | Interpret opportunity search requirements, formulate search strategy, call search tools, collect and return structured opportunities. |
| **Inputs** | Search criteria (role, location, work_mode, stipend range), student preferences |
| **Outputs** | List of normalized `Opportunity` records |
| **Tools** | `search_opportunities`, `fetch_opportunity_details`, `normalize_opportunity`, `deduplicate_opportunities`, `save_opportunity`, `create_audit_event` |
| **Constraints** | Must NOT fabricate opportunities. Must NOT bypass the OpportunityProvider abstraction. Must NOT directly access external APIs. |
| **Failure Behavior** | If API fails → record error, return partial results with status. If no results → report honestly, suggest broadening criteria. |
| **Termination Condition** | When search results have been collected, normalized, deduplicated, and returned. |

---

## 3. Eligibility Verification Agent

| Field | Specification |
|-------|---------------|
| **Purpose** | Interpret eligibility requirements from opportunity data, apply deterministic eligibility rules, and classify each opportunity as PASS / FAIL / UNKNOWN for the student. |
| **Inputs** | Student profile, list of opportunities with eligibility requirements |
| **Outputs** | List of eligibility verdicts with reasons |
| **Tools** | `check_eligibility`, `create_audit_event` |
| **Constraints** | Must NOT fabricate eligibility requirements that don't exist. Must NOT guess when data is missing — use UNKNOWN. Must use deterministic checks for numerical/date criteria. |
| **Failure Behavior** | If eligibility requirements are ambiguous → classify as UNKNOWN with explanation. If student profile is incomplete → flag missing fields. |
| **Termination Condition** | When all provided opportunities have been assessed. |

---

## 4. Application Processing Agent

| Field | Specification |
|-------|---------------|
| **Purpose** | Prepare application drafts, populate application fields, identify missing information, prepare documents, and request human approval before any consequential action. |
| **Inputs** | Student profile, selected opportunity, resume data |
| **Outputs** | Draft application, list of missing fields, approval request |
| **Tools** | `create_application_draft`, `read_resume`, `request_human_approval`, `save_application`, `create_audit_event` |
| **Constraints** | Must NEVER silently submit an application. Must NEVER proceed without explicit human approval. Must NOT fabricate application content. |
| **Failure Behavior** | If resume data is insufficient → list missing items and ask user. If approval is rejected → record rejection, do not proceed. |
| **Termination Condition** | When draft is prepared and either approved + submitted, or rejected + recorded. |

---

## 5. Approval Agent

| Field | Specification |
|-------|---------------|
| **Purpose** | Identify actions requiring human approval, create approval requests, record approval/rejection decisions, and enforce approval gates. |
| **Inputs** | Action requiring approval, context (what will happen if approved) |
| **Outputs** | Approval record (approved / rejected / pending) |
| **Tools** | `request_human_approval`, `create_audit_event` |
| **Constraints** | Must NEVER bypass an approval gate. Must NEVER auto-approve. Expired or missing approval must block execution. |
| **Failure Behavior** | If approval times out → status remains pending, action is blocked. |
| **Termination Condition** | When approval decision is recorded. |

---

## 6. Progress Tracking Agent

| Field | Specification |
|-------|---------------|
| **Purpose** | Track milestones during an active internship, detect incomplete tasks, summarize progress, and generate reminders. |
| **Inputs** | Application record, milestone data |
| **Outputs** | Progress summary, action recommendations, reminders |
| **Tools** | `update_progress`, `get_application_status`, `create_audit_event` |
| **Constraints** | Must NOT fabricate progress. Must NOT mark milestones complete without evidence. |
| **Failure Behavior** | If milestone data is missing → report as not_started with explanation. |
| **Termination Condition** | When progress summary is generated. |

---

## 7. Evaluation Agent

| Field | Specification |
|-------|---------------|
| **Purpose** | Organize evidence from the internship, evaluate using a defined rubric, generate a draft evaluation, and explain reasoning. |
| **Inputs** | Application record, progress data, evidence, rubric |
| **Outputs** | Draft evaluation with score and explanation |
| **Tools** | `create_audit_event` |
| **Constraints** | Must NOT bypass human authority for official grading. Draft scores are suggestions only. Must NOT fabricate evidence. |
| **Failure Behavior** | If evidence is insufficient → generate partial evaluation with confidence level. |
| **Termination Condition** | When draft evaluation is generated and presented for human review. |

---

## Implementation Status

| Agent | Lab | Status |
|-------|-----|--------|
| Coordinator | Lab 1 | ⬜ Not Started |
| Opportunity Discovery | Lab 2 | ⬜ Not Started |
| Eligibility Verification | Lab 2 | ⬜ Not Started |
| Application Processing | Lab 2+ | ⬜ Not Started |
| Approval | Lab 2+ | ⬜ Not Started |
| Progress Tracking | Future | ⬜ Not Started |
| Evaluation | Future | ⬜ Not Started |
