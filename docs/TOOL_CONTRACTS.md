# InternPilot — Tool Contracts

**Version:** 0.1.0  
**Last Updated:** 2026-10-05  
**Phase:** 0 — Foundation  

---

## Overview

Tools are deterministic capabilities that agents can invoke. Agents decide
WHEN to use them; tools perform the actual action. Every tool has a defined
schema, validation rules, and error behavior.

---

## Contract Template

| Field | Description |
|-------|-------------|
| **Name** | Tool identifier |
| **Purpose** | What this tool does |
| **Parameters** | Input schema |
| **Returns** | Output schema |
| **Validation** | Input constraints |
| **Error Behavior** | What happens on failure |
| **Authorization** | Who can call this tool |

---

## Tool Definitions

### read_resume
| Field | Specification |
|-------|---------------|
| Purpose | Read and extract text from a resume file |
| Parameters | `file_path: string` |
| Returns | `{ text: string, file_name: string, file_type: string }` |
| Validation | File must exist, supported format (PDF/DOCX/TXT) |
| Error Behavior | FileNotFound → error with message. UnsupportedFormat → error |
| Authorization | Coordinator, Application Processing Agent |

### get_candidate_profile
| Field | Specification |
|-------|---------------|
| Purpose | Retrieve the student's structured profile |
| Parameters | `student_id: UUID` |
| Returns | `Student` model with skills and preferences |
| Validation | student_id must exist |
| Error Behavior | NotFound → return null with status |
| Authorization | All agents |

### update_candidate_profile
| Field | Specification |
|-------|---------------|
| Purpose | Update student profile fields |
| Parameters | `student_id: UUID, updates: dict` |
| Returns | `{ success: bool, updated_fields: list }` |
| Validation | student_id must exist, fields must be valid |
| Error Behavior | ValidationError → return error with invalid fields |
| Authorization | Coordinator Agent (with user confirmation) |

### get_preferences
| Field | Specification |
|-------|---------------|
| Purpose | Retrieve student's internship preferences |
| Parameters | `student_id: UUID` |
| Returns | `CandidatePreference` model |
| Validation | student_id must exist |
| Error Behavior | NotFound → return empty preference with status |
| Authorization | All agents |

### search_opportunities
| Field | Specification |
|-------|---------------|
| Purpose | Search for internship opportunities via configured providers |
| Parameters | `query: string, location: string?, work_mode: string?, min_stipend: int?, max_results: int?` |
| Returns | `{ opportunities: List[RawOpportunity], source: string, count: int }` |
| Validation | query must be non-empty |
| Error Behavior | APIError → return partial results + error status. Timeout → return empty + error |
| Authorization | Opportunity Discovery Agent |

### normalize_opportunity
| Field | Specification |
|-------|---------------|
| Purpose | Normalize raw opportunity data into a standard schema |
| Parameters | `raw_opportunity: dict, source: string` |
| Returns | `Opportunity` model |
| Validation | Must have at minimum company and role |
| Error Behavior | Missing required fields → return partial with warnings |
| Authorization | Opportunity Discovery Agent |

### check_eligibility
| Field | Specification |
|-------|---------------|
| Purpose | Deterministic eligibility check for a student–opportunity pair |
| Parameters | `student: Student, opportunity: Opportunity` |
| Returns | `{ eligible: PASS/FAIL/UNKNOWN, reasons: List[string], missing_info: List[string] }` |
| Validation | Both student and opportunity must be provided |
| Error Behavior | Missing student data → UNKNOWN with explanation |
| Authorization | Eligibility Verification Agent |

### calculate_match_score
| Field | Specification |
|-------|---------------|
| Purpose | Compute structured match score between student and opportunity |
| Parameters | `student: Student, opportunity: Opportunity` |
| Returns | `OpportunityMatch` model |
| Validation | Both must be provided with sufficient data |
| Error Behavior | Insufficient data → partial score with confidence indicator |
| Authorization | Eligibility Verification Agent, Coordinator |

### request_human_approval
| Field | Specification |
|-------|---------------|
| Purpose | Create an approval request for a consequential action |
| Parameters | `action: string, context: dict, urgency: string?` |
| Returns | `{ approval_id: UUID, status: pending }` |
| Validation | action must be non-empty |
| Error Behavior | Always succeeds in creating the request |
| Authorization | Application Processing Agent, Approval Agent |

### create_audit_event
| Field | Specification |
|-------|---------------|
| Purpose | Record an audit event for any meaningful action |
| Parameters | `trace_id: string, actor_type: string, action: string, tool: string?, status: string, metadata: dict?` |
| Returns | `{ event_id: UUID }` |
| Validation | trace_id, actor_type, action, status are required |
| Error Behavior | Logging failure should not crash the workflow |
| Authorization | All agents |

---

## Implementation Status

| Tool | Phase | Status |
|------|-------|--------|
| read_resume | 2 | ✅ TXT reader implemented; upload ingestion supports TXT/PDF/DOCX |
| get_candidate_profile | 2 | ⬜ Not Started |
| update_candidate_profile | 2 | ✅ Implemented via MemoryManager/CandidatePreference |
| get_preferences | 2 | ✅ Implemented via PreferenceRepository |
| search_opportunities | 3 | ✅ Adzuna & Mock providers implemented |
| normalize_opportunity | 3 | ⬜ Not Started |
| check_eligibility | 3 | ⬜ Not Started |
| calculate_match_score | 3 | ⬜ Not Started |
| request_human_approval | 3+ | ⬜ Not Started |
| create_audit_event | 2 | ✅ Implemented internally for Lab 1–2 actions |
