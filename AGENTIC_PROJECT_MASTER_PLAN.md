# AGENTIC PROJECT MASTER PLAN
# InternPilot — Agentic Internship Discovery, Application & Tracking Platform

---

# 0. ROLE AND OPERATING MODE

You are the primary implementation engineering system for this project.

You are not being asked to produce a quick college demo.

You are building a real, extensible Agentic AI application that must:

1. satisfy the course Worklet 10 requirements,
2. implement Labs 1–5 progressively,
3. remain architecturally extensible for Labs 6–14,
4. demonstrate genuine Agentic AI concepts,
5. be useful to real students,
6. be understandable and defensible in a technical interview,
7. prioritize system architecture, reliability, observability, security and clear separation of responsibilities,
8. avoid fake or superficial multi-agent behavior.

You may use as many internal sub-agents, coding agents, review agents, test agents, debugging agents and documentation agents as useful.

Use as much reasoning, analysis and tool usage as necessary.
Do not prematurely stop because the task appears large.

However:

- Do not invent requirements.
- Do not silently change architectural decisions.
- Do not claim something is complete without verification.
- Do not skip tests because implementation appears obvious.
- Do not move to the next major step if the current step has not been verified.
- Do not create unnecessary complexity merely to make the project look "advanced".
- Prefer a smaller correct architecture over a larger fragile one.
- Every major architectural decision must have a reason.
- Every major component must have a clearly defined responsibility.
- Every autonomous action must have explicitly defined permissions.

You are allowed to create and coordinate multiple internal implementation/review agents.

A typical internal team may include:

- Architecture Agent
- Implementation Agent
- Testing Agent
- Code Review Agent
- Security Agent
- Agentic AI Review Agent
- Documentation Agent
- Debugging Agent
- UX Review Agent
- Integration Agent

You may create more specialized roles when useful.

The human owner of the project remains the final authority for major architectural decisions.

---

# 1. WHAT WE ARE BUILDING

## Product Name

InternPilot

## Full Title

Agentic Internship Discovery, Application & Tracking Platform

## One-Line Description

An Agentic AI platform that helps a student discover relevant internship opportunities, verify eligibility, evaluate personal fit, research opportunities, prepare applications, track application progress, and eventually track the internship through final evaluation in one auditable record.

---

# 2. THE REAL PROBLEM

Students often have:

- resumes stored as PDFs,
- skills distributed across resumes and projects,
- unclear eligibility for internships,
- large numbers of internship postings,
- difficulty comparing opportunities,
- difficulty remembering deadlines,
- difficulty tracking applications,
- difficulty identifying skill gaps,
- difficulty researching companies,
- difficulty deciding which opportunities deserve attention.

The system should reduce this fragmented workflow.

The student should be able to provide:

- resume,
- academic information,
- preferences,
- target roles,
- location preferences,
- stipend preferences,
- availability,
- optional career goals.

The system should then help with:

1. understanding the student's goal,
2. discovering opportunities,
3. normalizing opportunity information,
4. determining eligibility,
5. calculating candidate-opportunity fit,
6. researching promising opportunities,
7. preparing application material,
8. requesting human approval before consequential actions,
9. tracking the application lifecycle,
10. eventually tracking internship progress and evaluation.

---

# 3. PRODUCT PHILOSOPHY

This is NOT:

User
→ ChatGPT
→ internship list

This IS:

Student
→ Agentic reasoning
→ Tools
→ External data
→ Structured state
→ Deterministic business logic
→ Semantic matching
→ Memory
→ Research
→ Human approval
→ Tracking
→ Audit trail

The system must demonstrate that Agentic AI is being used because the problem requires:

- goal interpretation,
- planning,
- tool selection,
- multi-step execution,
- observation,
- state management,
- conditional decisions,
- memory,
- external system interaction,
- human-in-the-loop control.

---

# 4. CORE ARCHITECTURAL PRINCIPLE

Always separate:

## LLM Responsibilities

Use LLMs for:

- natural language understanding,
- intent interpretation,
- clarification,
- resume information extraction,
- job-description interpretation,
- semantic skill interpretation,
- research synthesis,
- personalized explanations,
- draft generation,
- ambiguous reasoning,
- natural-language interaction.

## Deterministic Responsibilities

Use normal application logic for:

- eligibility rules,
- numerical comparison,
- CGPA checks,
- date calculations,
- deadline calculations,
- authentication,
- authorization,
- database writes,
- application status,
- permissions,
- audit records,
- approval state,
- final official values.

## Database Responsibilities

Store:

- student profile,
- candidate preferences,
- resumes,
- opportunities,
- normalized opportunity records,
- applications,
- progress,
- evaluations,
- memory,
- approvals,
- audit events.

## Human Responsibilities

The system must keep a human as the authority for consequential actions.

Examples:

- final application submission,
- sensitive information disclosure,
- official evaluation,
- official grading,
- destructive actions,
- high-risk external actions.

---

# 5. TARGET ARCHITECTURE

The architecture should evolve progressively.

Initial conceptual architecture:

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

Long-term target:

                         STUDENT
                            |
                            v
                      React Frontend
                            |
                            v
                      FastAPI API
                            |
                            v
                  Agent Runtime / Graph
                            |
                 +----------+----------+
                 |                     |
                 v                     v
             Coordinator             Memory
                 |
       +---------+----------+----------------+
       |         |          |                |
       v         v          v                v
   Discovery Eligibility Application     Tracking
      Agent      Agent      Agent          Agent
       |           |          |              |
       +-----------+----------+--------------+
                   |
                   v
             Research Agent
                   |
                   v
             Match / Ranking
                   |
                   v
             Human Approval
                   |
                   v
             External Actions
                   |
                   v
              Audit Layer
                   |
                   v
              Final Record

The architecture must be implemented incrementally.

Do not prematurely build the entire final system.

---

# 6. TECHNOLOGY DIRECTION

Use the following technology direction unless a strong technical reason requires an alternative.

## Frontend

- React
- TypeScript
- Tailwind CSS or an equally maintainable UI system

## Backend

- Python
- FastAPI
- Pydantic

## Agent Layer

Primary direction:

- LangGraph for stateful orchestration and graph-based workflows
- LangChain for model/tool/agent building blocks where useful

Do not use frameworks just for decoration.

## LLM

Use an abstraction layer so the application is not tied to one model provider.

Initial development may use:

- Ollama/local model where practical

The architecture must allow switching to:

- cloud LLM providers
- another local model
- another inference service

without redesigning the entire application.

The model provider must never be hard-coded deep inside business logic.

## Database

Initial:

- SQLite

Design repositories/interfaces so migration to PostgreSQL is straightforward later.

## Search / Opportunity Sources

Do not hard-code the entire system around one external job provider.

Create an abstraction:

OpportunityProvider

Possible implementations:

- job aggregation API
- web-search provider
- additional approved job API
- mock provider for development/testing

The exact providers may be selected and configured during implementation.

Do not assume one provider will provide complete internship coverage.

## MCP

Implement a clean MCP-style connector architecture for Lab 5.

The connector must eventually provide controlled access to:

- files,
- SQLite/database,
- external opportunity API.

## n8n

n8n is NOT the core Agentic AI orchestrator.

It may later be used for:

- scheduled ingestion,
- notifications,
- reminders,
- external automation,
- integrations.

Do not make the project's core agent reasoning dependent on n8n.

---

# 7. IMPORTANT ARCHITECTURAL RULE:
# PROVIDER ABSTRACTION

Do NOT write:

agent
→ Adzuna-specific code
→ database

Instead:

agent
→ OpportunitySearchTool
→ OpportunityProvider interface
→ selected provider

For example:

OpportunityProvider
|
+-- AdzunaProvider
+-- JSearchProvider
+-- WebSearchProvider
+-- MockOpportunityProvider

This allows the system to evolve without rewriting the agent architecture.

---

# 8. CORE DOMAIN ENTITIES

Design the data model around the following entities.

## Student

Fields may include:

- student_id
- name
- email
- branch
- degree
- graduation_year
- cgpa
- resume reference
- profile metadata

## CandidateSkill

- student_id
- skill
- proficiency
- source
- confidence

## CandidatePreference

- student_id
- target_roles
- locations
- work_modes
- minimum_stipend
- duration_preferences
- availability
- additional_constraints

## Resume

- resume_id
- student_id
- file_reference
- version
- extracted_text_reference
- parsed_profile
- created_at

## Opportunity

- opportunity_id
- source
- source_id
- company
- role
- description
- location
- work_mode
- stipend
- duration
- deadline
- eligibility requirements
- required skills
- application URL
- fetched_at
- normalized data

## OpportunityMatch

- student_id
- opportunity_id
- eligibility
- eligibility_reason
- skill_match
- role_match
- location_match
- preference_match
- deadline_risk
- overall_score
- missing_skills
- explanation

## Application

- application_id
- student_id
- opportunity_id
- status
- resume_version
- draft_application
- approval_state
- submission_reference
- timestamps

## Progress

- application_id
- milestone
- status
- start date
- end date
- notes
- evidence

## Evaluation

- application_id
- mentor feedback
- company feedback
- rubric
- draft score
- final score
- final grade
- approved_by

## AuditEvent

Every meaningful agent/tool/action event should be representable.

Fields may include:

- event_id
- trace_id
- timestamp
- actor_type
- actor_id
- agent
- action
- tool
- input_reference
- output_reference
- approval_state
- status
- error
- metadata

---

# 9. AGENT DEFINITIONS

Do not create agents merely because the word "agent" sounds impressive.

Each agent must have:

1. clear responsibility,
2. defined input,
3. defined output,
4. allowed tools,
5. forbidden actions,
6. state dependencies,
7. failure behavior.

Initial agents:

## Coordinator Agent

Responsibilities:

- understand high-level goal,
- manage workflow,
- initialize state,
- route tasks,
- handle exceptions,
- determine next stage,
- coordinate specialized capabilities.

It must NOT directly own every specialized operation.

## Opportunity Discovery Agent

Responsibilities:

- interpret opportunity search requirements,
- formulate search strategy,
- call opportunity-search tools,
- collect candidate opportunities,
- request normalization,
- request deduplication,
- return structured opportunities.

## Eligibility Verification Agent

Responsibilities:

- interpret eligibility requirements,
- call deterministic eligibility rules,
- identify PASS / FAIL / UNKNOWN,
- explain reasons,
- flag missing information.

It must NOT fabricate missing requirements.

## Application Processing Agent

Responsibilities:

- prepare application drafts,
- populate application fields,
- identify missing information,
- prepare documents,
- request approval before consequential action.

It must NOT silently submit applications.

## Approval Agent

Responsibilities:

- identify actions requiring human approval,
- create approval requests,
- record approval/rejection,
- prevent execution without required approval.

## Progress Tracking Agent

Responsibilities:

- track milestones,
- detect incomplete tasks,
- summarize application/internship progress,
- generate reminders or action recommendations.

## Evaluation Agent

Responsibilities:

- organize evidence,
- evaluate using a defined rubric,
- generate draft evaluation,
- explain reasoning.

It must NOT bypass human authority for official grading.

---

# 10. TOOLS

Tools are capabilities.

Agents decide WHEN to use them.

Tools perform deterministic/external actions.

Possible tools:

- read_resume
- read_file
- extract_document_text
- get_candidate_profile
- update_candidate_profile
- get_preferences
- search_opportunities
- fetch_opportunity_details
- normalize_opportunity
- deduplicate_opportunities
- check_eligibility
- calculate_match_score
- calculate_deadline_risk
- save_opportunity
- create_application_draft
- request_human_approval
- save_application
- get_application_status
- update_progress
- create_audit_event

Every tool must define:

- name,
- purpose,
- parameters,
- return schema,
- validation,
- error behavior,
- authorization requirements.

---

# 11. SKILLS

A skill is a reusable capability package.

Initial skill:

## Internship Research Skill

Input:

- opportunity
- optional research objective

Output:

- company
- role
- location
- work mode
- stipend
- duration
- deadline
- eligibility
- skills
- application process
- company context
- important observations
- evidence/source references
- confidence

The skill must be reusable by more than one workflow.

Do not implement skills as random prompts scattered throughout the codebase.

Create a clear skill abstraction.

---

# 12. MEMORY ARCHITECTURE

We need two distinct concepts.

## Session State

Temporary state for the current workflow/conversation.

Example:

- current user request,
- current search preferences,
- current opportunities,
- current workflow stage,
- current approval request.

## Persistent Memory / Stored Reference

Information that should remain available later.

Examples:

- preferred roles,
- preferred locations,
- minimum stipend,
- career interests,
- previous applications,
- rejected opportunities,
- profile preferences.

Do not confuse conversation history with long-term structured memory.

Use structured storage wherever possible.

---

# 13. OPPORTUNITY INGESTION ARCHITECTURE

The system must eventually support:

                Opportunity Search
                        |
           +------------+------------+
           |            |            |
           v            v            v
        API #1       API #2      Web Search
           |            |            |
           +------------+------------+
                        |
                        v
               Raw Opportunity Data
                        |
                        v
             Opportunity Normalizer
                        |
                        v
                 Deduplication
                        |
                        v
                Opportunity DB
                        |
                        v
             Eligibility / Matching

Do not allow every agent to independently scrape or fetch the Internet.

Centralize external opportunity acquisition behind tools/providers.

---

# 14. RESUME ARCHITECTURE

The resume lifecycle should be:

Student
→ upload PDF/DOCX
→ backend stores original file
→ text extraction
→ resume parser
→ structured CandidateProfile
→ validation
→ persistent storage

The original resume must remain preserved.

The parsed profile is a derived representation.

The system must be able to identify:

- information source,
- parsing confidence where applicable,
- resume version.

Do not overwrite the original document with extracted content.

---

# 15. MATCHING ARCHITECTURE

Eligibility and matching are different.

Eligibility answers:

"Can this student apply?"

Matching answers:

"How suitable is this opportunity for this student?"

Eligibility should use deterministic logic where possible.

Examples:

- CGPA thresholds,
- graduation year,
- branch,
- location constraints,
- explicit experience requirements.

Semantic matching can use LLM/embeddings for:

- skill equivalence,
- role similarity,
- project relevance,
- experience relevance.

Ranking should be based on structured signals.

Do NOT make the overall score an arbitrary number invented by the LLM.

Every score must be explainable.

Example:

Skill Match: 88%
Role Match: 94%
Location Fit: 100%
Preference Fit: 91%
Deadline Risk: Low

Overall Match: 91%

The exact formula should be defined during implementation and documented.

---

# 16. HUMAN-IN-THE-LOOP ARCHITECTURE

Important actions must use explicit approval.

Example:

Application Preparation
→ Draft generated
→ Human reviews
→ Human approves
→ Submission tool executes

Never:

LLM
→ automatically submit an application
→ without explicit authorization.

Approval state must be persisted.

Expired/missing/rejected approval must block execution.

---

# 17. AUDITABILITY

We need the ability to explain:

- what the agent did,
- which tool it called,
- when it called it,
- what input was used,
- what result came back,
- what state changed,
- whether human approval existed.

Example trace:

TRACE-001

09:42:01 Coordinator initialized
09:42:02 get_candidate_profile()
09:42:03 read_resume()
09:42:05 search_opportunities()
09:42:07 normalize_opportunity()
09:42:10 check_eligibility()
09:42:12 calculate_match_score()
09:42:15 research_opportunity()
09:42:20 final ranking generated

Do not fake traces.

They must represent actual execution.

---

# 18. ERROR HANDLING

Agents must not assume tools always work.

Examples:

- external API unavailable,
- malformed resume,
- invalid JSON,
- incomplete job description,
- missing eligibility requirement,
- expired internship,
- duplicate listing,
- database failure,
- model failure,
- tool timeout,
- unauthorized action.

The system should:

1. detect failure,
2. record it,
3. retry when appropriate,
4. use fallback only when explicitly designed,
5. never silently fabricate missing data,
6. expose uncertainty to the user.

Use:

PASS
FAIL
UNKNOWN

where appropriate.

"UNKNOWN" is preferable to a fabricated decision.

---

# 19. SECURITY

Secrets must never be hard-coded.

Use environment variables.

Examples:

LLM API key
Search API key
Job provider credentials
Database credentials

Never commit `.env`.

Provide `.env.example`.

The frontend must never receive backend-only API keys.

Agent tools must use authorization boundaries.

Agents should only receive the capabilities they require.

---

# 20. DEVELOPMENT PHILOSOPHY

Do not build everything at once.

Build a thin vertical slice.

Each lab must become a real feature of InternPilot.

Do not create five independent mini-projects.

The same system must evolve.

---

# 21. THE MASTER LOOP

THIS IS THE MOST IMPORTANT INSTRUCTION.

For EVERY major implementation step, follow this exact loop:

## LOOP

### STEP 1 — PLAN

Before modifying code:

- inspect the existing repository,
- inspect current architecture,
- inspect relevant documents,
- determine what already exists,
- identify dependencies,
- identify files that need changes,
- identify risks,
- define acceptance criteria.

If another architecture decision is required, make the smallest decision consistent with this document.

Do not rewrite unrelated components.

---

### STEP 2 — IMPLEMENT

Implement only the current milestone.

Write production-quality code.

Keep interfaces clean.

Add tests for important behavior.

Update documentation.

Do not prematurely implement future labs unless a small abstraction is genuinely required for extensibility.

---

### STEP 3 — RUN

Actually execute:

- application,
- unit tests,
- integration tests,
- type checks where available,
- linting where available,
- relevant API calls,
- agent workflows.

Do not assume success.

---

### STEP 4 — VERIFY

Verify against explicit acceptance criteria.

Verify:

- functional correctness,
- architectural correctness,
- data flow,
- tool usage,
- agent behavior,
- error handling,
- security,
- persistence,
- user experience.

Ask:

"Did the implementation actually satisfy the intended concept?"

Not merely:

"Did the code run?"

---

### STEP 5 — DEBUG

If anything fails:

- inspect the real error,
- identify root cause,
- fix it,
- rerun tests,
- rerun the complete relevant workflow.

Do not stop after making a speculative fix.

---

### STEP 6 — RE-VERIFY

The milestone is NOT complete until:

- tests pass,
- integration works,
- the workflow has been executed,
- expected outputs are observed,
- architectural constraints are satisfied.

---

### STEP 7 — DOCUMENT

Update:

- README,
- architecture documentation,
- agent contracts,
- tool contracts,
- data model documentation,
- lab progress,
- known limitations,
- test results.

Record important architecture decisions.

---

### STEP 8 — ONLY THEN MOVE TO NEXT STEP

Never jump from:

Implement
→ "looks fine"
→ next lab

Instead:

Implement
→ Verify
→ Fix
→ Re-verify
→ Document
→ Next milestone

---

# 22. LOOP FAILURE RULE

If verification fails:

DO NOT proceed to the next milestone.

Repeat:

PLAN
→ IMPLEMENT/FIX
→ RUN
→ VERIFY

until the current milestone satisfies acceptance criteria.

If a blocking issue cannot be solved without a major architectural change:

1. stop,
2. document the conflict,
3. identify the architectural decision required,
4. preserve working code,
5. do not silently redesign unrelated components.

---

# 23. LAB ROADMAP

The first five labs are mandatory for the immediate review.

The implementation must map each lab into InternPilot.

---

# LAB 1 — AGENT VS CHATBOT

Goal:

Demonstrate that InternPilot can behave as an agent rather than a simple chatbot.

Required behavior:

User:
"I want an AI internship."

System should determine whether information is missing.

It may ask for:

- graduation year,
- target role,
- location,
- stipend,
- preferences.

It should:

1. clarify,
2. maintain state,
3. formulate a plan,
4. execute when enough information exists,
5. revise when required.

Do NOT implement a fake "agent" consisting only of a prompt that says "you are an agent."

Acceptance criteria:

- conversational state exists,
- clarification happens when needed,
- user request is converted into structured intent,
- agent can determine next action,
- workflow is observable.

---

# LAB 2 — TOOL-USING AGENT

Add real tools.

Minimum useful tools:

- calculator tool,
- file reader/resume reader,
- internship search tool.

The agent must be capable of deciding when to call a tool.

Demonstrate:

User:
"Find AI internships in Bangalore."

Agent:
→ calls internship search tool.

User:
"Read my resume."

Agent:
→ calls resume/file tool.

Tool results must be returned to the agent.

The system must distinguish:

LLM reasoning
from
tool execution.

Acceptance criteria:

- tools have schemas,
- tool calls are observable,
- arguments are validated,
- tool results are returned,
- failures are handled,
- no fake tool calls exist.

---

# LAB 3 — SKILL CREATION

Create the reusable Internship Research Skill.

The skill must be reusable.

It should accept a structured opportunity or source and return a structured research result.

Demonstrate that the skill is a reusable capability rather than a prompt duplicated across agents.

Acceptance criteria:

- clear input schema,
- clear output schema,
- reusable implementation,
- evidence/source handling,
- error handling,
- documented contract.

---

# LAB 4 — MEMORY & RETRIEVAL

Implement:

1. session state,
2. persistent candidate preferences.

Example:

Session:

User:
"I want Bangalore internships."

Later in another session:

User:
"Find internships for me."

The system should retrieve persistent preferences where appropriate.

Clearly distinguish:

Session State
vs
Persistent Memory.

Acceptance criteria:

- memory is actually persisted,
- retrieval is demonstrated,
- state is not solely dependent on chat history,
- data ownership is clear,
- retrieval behavior is testable.

---

# LAB 5 — MCP-STYLE CONNECTOR

Implement the connector layer.

The connector must expose controlled access to:

1. File operations
2. SQLite/database
3. External API

Conceptually:

Agent
→ Connector
→ Files / SQLite / API

The agent should not directly couple every part of the application to every backend system.

Implement clear tool/resource interfaces.

The architecture should remain compatible with a future real MCP implementation or extension.

Acceptance criteria:

- file capability available,
- SQLite capability available,
- API capability available,
- common connector boundary exists,
- access is controlled,
- errors propagate correctly,
- calls are logged/auditable.

---

# 24. AFTER LAB 5

Do not implement all future labs immediately.

However, preserve architecture for:

Lab 6:
Agent runtime, skills, tools, memory, audit log

Lab 7:
Agentic node graph

Lab 8:
Parallel multi-agent swarm

Lab 9:
Deep research

Lab 10:
Cloud operations

Lab 11:
Agentic SDLC

Lab 12:
Safety & governance

Lab 13:
Discipline-specific agents

Lab 14:
Full capstone

The architecture must make these extensions possible without a complete rewrite.

---

# 25. FUTURE AGENT GRAPH

Eventually target a graph similar to:

START
  |
  v
Coordinator
  |
  v
Profile / Intent
  |
  v
Discovery
  |
  v
Eligibility
  |
  v
Matching
  |
  v
Research
  |
  v
Application Preparation
  |
  v
Human Approval
  |
  v
Submission
  |
  v
Tracking
  |
  v
Evaluation
  |
  v
END

With conditional branches for:

- missing information,
- ineligible candidate,
- API failure,
- insufficient opportunity data,
- approval rejection,
- expired opportunity,
- tool failure.

---

# 26. FUTURE MULTI-AGENT SWARM

Eventually allow parallel specialist agents such as:

Discovery Agent
Eligibility Agent
Skill Matching Agent
Company Research Agent
Application Agent

A coordinator merges their outputs.

The system should demonstrate:

- parallel work,
- structured outputs,
- merge,
- conflict detection,
- final synthesis.

Do NOT implement this as meaningless agents talking to each other.

Every agent must have a real reason to exist.

---

# 27. FUTURE DEEP RESEARCH

Research workflows should support:

question
→ search
→ collect evidence
→ compare
→ synthesize
→ cite sources
→ confidence

The user should be able to inspect evidence behind important research results.

---

# 28. FUTURE GOVERNANCE

Eventually include:

- permissions,
- approval gates,
- audit logs,
- evaluation,
- rollback where meaningful,
- privacy controls,
- confidence/uncertainty,
- tool restrictions.

The system should never silently bypass an approval gate.

---

# 29. UI DIRECTION

The UI should be simple and useful.

Main areas:

## Dashboard

- recommended internships,
- application statuses,
- approaching deadlines,
- skill gaps,
- current tasks.

## Profile

- academic profile,
- skills,
- preferences,
- resume versions.

## Opportunity Explorer

Each opportunity should show:

- role,
- company,
- location,
- stipend,
- deadline,
- eligibility,
- match score,
- skill gap,
- source,
- research,
- application status.

## Agent Activity / Trace

Show a human-readable trace.

Example:

Coordinator
→ Read profile
→ Search opportunities
→ Checked eligibility
→ Ranked results
→ Researched top opportunities

## Applications

Track:

- draft,
- approval,
- submitted,
- interview,
- selected,
- rejected,
- withdrawn.

---

# 30. NON-FUNCTIONAL REQUIREMENTS

The system should prioritize:

- modularity,
- readability,
- testability,
- observability,
- security,
- reliability,
- maintainability,
- explainability,
- extensibility.

Do not optimize for maximum number of files.

Do not optimize for maximum number of agents.

Do not optimize for framework count.

Optimize for engineering quality.

---

# 31. TESTING STRATEGY

Every important feature requires tests.

Include:

## Unit tests

For:

- eligibility rules,
- parsing,
- normalization,
- matching,
- deadline calculations,
- memory operations.

## Integration tests

For:

- agent → tool,
- agent → database,
- connector → SQLite,
- connector → file,
- connector → API.

## Agent behavior tests

Test:

- correct tool selection,
- incorrect tool parameters,
- missing information,
- ambiguous requests,
- failed tools,
- invalid data.

## Safety tests

Test:

- unauthorized submission,
- missing approval,
- expired approval,
- malformed input,
- prompt injection in external content,
- attempts to access unauthorized tools.

---

# 32. PROMPT / AGENT CONTRACTS

Every production agent should have:

## Purpose

What it exists to do.

## Inputs

What state/data it receives.

## Outputs

What structured result it produces.

## Tools

What it is allowed to call.

## Constraints

What it must not do.

## Failure behavior

What happens when information is missing or a tool fails.

## Termination condition

When the agent should stop.

Avoid vague prompts.

Agents should produce structured outputs whenever possible.

---

# 33. OBSERVABILITY REQUIREMENTS

Introduce trace IDs.

Every major workflow must be traceable.

Example:

TRACE-ID:
RUN-2026-001

Steps:

Coordinator
Discovery Agent
search_opportunities
Eligibility Agent
check_eligibility
Match Engine
Research Agent
Final Response

The trace should make debugging possible.

---

# 34. DOCUMENTATION REQUIREMENTS

Maintain:

/docs

ARCHITECTURE.md
AGENT_CONTRACTS.md
TOOL_CONTRACTS.md
DATA_MODEL.md
MEMORY_DESIGN.md
CONNECTOR_DESIGN.md
SECURITY.md
TESTING.md
LAB_PROGRESS.md

Also maintain an Architecture Decision Record folder:

/docs/ADR/

Use ADRs for major decisions such as:

- why LangGraph,
- why SQLite initially,
- why provider abstraction,
- why deterministic eligibility,
- why human approval,
- why MCP-style connector,
- why n8n is not the core orchestrator.

---

# 35. GIT STRATEGY

Use feature branches where practical.

Suggested progression:

main
|
+-- lab-1-agent
+-- lab-2-tools
+-- lab-3-skills
+-- lab-4-memory
+-- lab-5-connector

Keep commits meaningful.

Example:

feat(lab2): add internship search tool

feat(lab4): add persistent candidate preferences

feat(lab5): add connector layer

Do not commit secrets.

---

# 36. CODING-AGENT RULES

Before modifying code:

1. inspect existing files,
2. understand architecture,
3. identify dependencies,
4. identify tests.

When implementing:

- avoid unnecessary rewrites,
- preserve interfaces,
- add tests,
- use typed models,
- validate inputs,
- handle errors,
- update docs.

When finished:

- run tests,
- inspect logs,
- perform an end-to-end workflow,
- report actual results.

Never report:

"Everything works"

unless you actually ran the relevant verification.

---

# 37. ANTI-HALLUCINATION RULES

Never fabricate:

- internship listings,
- companies,
- eligibility,
- stipend,
- deadlines,
- URLs,
- API results.

If external data is unavailable:

say so.

If a field cannot be determined:

use UNKNOWN or null according to the schema.

Do not convert uncertainty into fake certainty.

---

# 38. ANTI-"FAKE AGENT" RULE

A component is not an agent simply because its class is named:

Agent.

To qualify as an agentic component, it should demonstrate some combination of:

- goal interpretation,
- decision making,
- tool selection,
- state,
- observation,
- conditional routing,
- planning,
- revision.

Do not create agents that simply execute one deterministic function with an unnecessary LLM call.

---

# 39. COST AND PERFORMANCE RULE

Use the cheapest reliable mechanism for each task.

Prefer:

deterministic code
before
LLM reasoning

Prefer:

metadata filtering
before
semantic matching

Prefer:

structured filters
before
expensive research

Prefer:

candidate shortlist
before
deep research

Do not send hundreds of raw job descriptions to an LLM unnecessarily.

---

# 40. FIRST IMPLEMENTATION TARGET

Do NOT begin by creating the full finished platform.

Begin with the smallest working vertical slice:

Student
→ Request
→ Agent
→ Search Tool
→ Internship Results

Then:

Student
→ Resume
→ Parsed Candidate Profile

Then:

Candidate Profile
+
Opportunities
→ Eligibility

Then:

Eligibility
+
Skills
→ Match

Then:

Match
→ Research Skill

Then:

Memory

Then:

MCP-style connector

Each addition must integrate with the existing system.

---

# 41. INITIAL END-TO-END DEMO TARGET

We eventually want this exact experience:

### Step 1

Student uploads resume.

### Step 2

System extracts candidate information.

### Step 3

Student confirms/edit profile.

### Step 4

Student says:

"Find AI/ML internships for me in Bangalore or remote, preferably paid."

### Step 5

Coordinator interprets the request.

### Step 6

Discovery Agent searches through configured opportunity sources.

### Step 7

Results are normalized and deduplicated.

### Step 8

Eligibility Agent checks objective requirements.

### Step 9

Match engine calculates candidate-opportunity fit.

### Step 10

Research Skill investigates top opportunities.

### Step 11

System presents ranked results.

Example:

1. AI/ML Intern — Company A
   Match: 91%
   Eligibility: PASS
   Missing skill: PyTorch
   Deadline: 5 days

2. Data Science Intern — Company B
   Match: 86%
   Eligibility: PASS

3. ML Intern — Company C
   Match: 78%
   Eligibility: UNKNOWN
   Reason: graduation requirement unclear

### Step 12

User selects one.

### Step 13

Application Agent prepares a draft.

### Step 14

Human approval is requested.

### Step 15

Only after approval can a consequential external action occur.

### Step 16

Application status is tracked.

---

# 42. DEVELOPMENT ORDER

Follow this order unless technical evidence requires a small adjustment:

PHASE 0
Repository + architecture + contracts

PHASE 1
Basic backend/frontend skeleton

PHASE 2
Lab 1 Agent

PHASE 3
Lab 2 Tools

PHASE 4
Resume ingestion

PHASE 5
Opportunity provider abstraction

PHASE 6
Lab 3 Internship Research Skill

PHASE 7
Lab 4 Memory

PHASE 8
Lab 5 MCP-style Connector

PHASE 9
End-to-end Lab 1–5 demo

Only after that:
Lab 6+

---

# 43. CURRENT PHASE

When this document is first loaded:

DO NOT immediately implement Labs 1–5 all at once.

First:

1. inspect repository,
2. inspect installed environment,
3. identify available runtimes,
4. inspect current files,
5. create architecture documentation,
6. create implementation plan,
7. create folder structure if needed,
8. verify prerequisites,
9. then begin Phase 1.

The first goal is to establish a clean project foundation.

---

# 44. EXECUTION LOOP FOR THE ENTIRE PROJECT

Repeat this loop for every milestone:

==================================================
LOOP START
==================================================

1. READ CURRENT STATE

2. PLAN CURRENT MILESTONE

3. DEFINE ACCEPTANCE CRITERIA

4. IMPLEMENT

5. RUN UNIT TESTS

6. RUN INTEGRATION TESTS

7. RUN END-TO-END WORKFLOW

8. INSPECT ACTUAL OUTPUT

9. CHECK ARCHITECTURE

10. CHECK SECURITY

11. FIX FAILURES

12. RE-RUN VERIFICATION

13. DOCUMENT RESULT

14. UPDATE LAB_PROGRESS.md

15. CREATE/UPDATE COMMIT

16. ONLY THEN START NEXT MILESTONE

==================================================
LOOP END

If verification fails:

DO NOT advance.

Repeat from step 2.

---

# 45. DEFINITION OF DONE

A milestone is DONE only when:

[ ] Feature implemented
[ ] Code runs
[ ] Unit tests pass
[ ] Integration tests pass where applicable
[ ] End-to-end flow verified
[ ] Errors handled
[ ] Security checked
[ ] Architecture still clean
[ ] Documentation updated
[ ] Acceptance criteria satisfied
[ ] Actual output inspected
[ ] No fake data presented as real
[ ] No unverified claims of completion

---

# 46. FINAL PRINCIPLE

This project should not merely demonstrate:

"I know how to use an LLM."

It should demonstrate:

"I know how to design, orchestrate, observe, evaluate and govern an Agentic AI system."

The final system should therefore reflect:

Agentic Reasoning
+
Tools
+
Skills
+
Memory
+
Connectors
+
State
+
Orchestration
+
Human Approval
+
Auditability
+
Deterministic Business Logic
+
Evaluation
+
Reliable Engineering

Build slowly.
Verify continuously.
Do not skip foundations.

The system must grow one verified layer at a time.

---

# 47. START COMMAND

When this document is provided to you, start by:

1. reading this entire document,
2. inspecting the existing repository,
3. creating the architecture and project foundation,
4. reporting the current state,
5. defining the first implementation milestone,
6. implementing it,
7. verifying it,
8. fixing failures,
9. documenting the result,
10. proceeding to the next milestone only after verification passes.

DO NOT ask me to manually implement basic code that you can implement yourself.

DO NOT dump a huge amount of code without verification.

DO NOT implement the whole project in one shot.

DO NOT skip directly to advanced multi-agent functionality.

WORK IN THE LOOP.

PLAN
→ IMPLEMENT
→ VERIFY
→ FIX
→ RE-VERIFY
→ DOCUMENT
→ NEXT STEP

Repeat until the project is complete.
