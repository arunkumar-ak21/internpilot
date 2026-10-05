# InternPilot — Data Model

**Version:** 0.1.0  
**Last Updated:** 2026-10-05  
**Phase:** 0 — Foundation  

---

## Overview

The data model is designed around the internship lifecycle: from student
profile creation through opportunity discovery, application, tracking,
and evaluation.

All models use Pydantic for validation and SQLAlchemy-compatible patterns
for persistence. The repository pattern ensures the database engine can
be swapped without touching business logic.

---

## Entity Relationship Diagram

```
┌─────────────┐     1:N     ┌──────────────────┐
│   Student    │◄────────────│  CandidateSkill  │
│             │             └──────────────────┘
│             │     1:1     ┌──────────────────────┐
│             │◄────────────│ CandidatePreference  │
│             │             └──────────────────────┘
│             │     1:N     ┌──────────────┐
│             │◄────────────│    Resume     │
│             │             └──────────────┘
│             │     1:N     ┌──────────────────┐
│             │◄────────────│ OpportunityMatch │
│             │             └──────────────────┘
│             │     1:N     ┌──────────────┐
│             │◄────────────│ Application  │
└─────────────┘             └──────┬───────┘
                                   │ 1:N
                                   v
                            ┌──────────────┐
                            │   Progress   │
                            └──────────────┘
                                   │ 1:1
                                   v
                            ┌──────────────┐
                            │  Evaluation  │
                            └──────────────┘

┌──────────────┐     N:1    ┌──────────────────┐
│ Application  │────────────►│   Opportunity    │
└──────────────┘            └──────────────────┘

┌──────────────────┐   N:1  ┌──────────────────┐
│ OpportunityMatch │────────►│   Opportunity    │
└──────────────────┘        └──────────────────┘

┌──────────────┐   (standalone, references any entity)
│  AuditEvent  │
└──────────────┘
```

---

## Entity Definitions

### Student

Primary entity representing a platform user.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| student_id | UUID | PK | Unique student identifier |
| name | string | required | Full name |
| email | string | required, unique | Contact email |
| branch | string | optional | Academic branch (e.g., CSE, ECE) |
| degree | string | optional | Degree program (e.g., B.Tech) |
| graduation_year | integer | optional | Expected graduation year |
| cgpa | float | optional, 0.0–10.0 | Current CGPA |
| created_at | datetime | auto | Account creation timestamp |
| updated_at | datetime | auto | Last update timestamp |

---

### CandidateSkill

Skills extracted from resume or manually added.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique record ID |
| student_id | UUID | FK → Student | Owner |
| skill | string | required | Skill name (e.g., "Python") |
| proficiency | string | optional | beginner / intermediate / advanced |
| source | string | required | "resume" / "manual" / "inferred" |
| confidence | float | optional, 0.0–1.0 | Extraction confidence |

---

### CandidatePreference

Student's internship search preferences.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique record ID |
| student_id | UUID | FK → Student, unique | Owner |
| target_roles | list[string] | optional | Desired roles |
| locations | list[string] | optional | Preferred locations |
| work_modes | list[string] | optional | remote / onsite / hybrid |
| minimum_stipend | integer | optional | Minimum acceptable stipend |
| duration_preferences | string | optional | e.g., "3-6 months" |
| availability | string | optional | e.g., "Jan 2027" |
| additional_constraints | string | optional | Free-text constraints |
| updated_at | datetime | auto | Last update timestamp |

---

### Resume

Uploaded resume files and their parsed representations.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| resume_id | UUID | PK | Unique resume ID |
| student_id | UUID | FK → Student | Owner |
| file_path | string | required | Path to original file |
| file_name | string | required | Original filename |
| version | integer | default 1 | Resume version number |
| extracted_text | text | optional | Raw extracted text |
| parsed_profile | JSON | optional | Structured parsed data |
| created_at | datetime | auto | Upload timestamp |

---

### Opportunity

An internship opportunity from any source.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| opportunity_id | UUID | PK | Unique opportunity ID |
| source | string | required | Provider name (e.g., "adzuna") |
| source_id | string | optional | ID from the source system |
| company | string | required | Company name |
| role | string | required | Role title |
| description | text | optional | Full description |
| location | string | optional | Location |
| work_mode | string | optional | remote / onsite / hybrid |
| stipend | string | optional | Stipend info (text or number) |
| duration | string | optional | Duration info |
| deadline | date | optional | Application deadline |
| eligibility_requirements | JSON | optional | Structured requirements |
| required_skills | list[string] | optional | Listed required skills |
| application_url | string | optional | URL to apply |
| fetched_at | datetime | auto | When fetched from source |
| normalized_data | JSON | optional | Normalized representation |

---

### OpportunityMatch

Computed match between a student and an opportunity.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique match ID |
| student_id | UUID | FK → Student | Student |
| opportunity_id | UUID | FK → Opportunity | Opportunity |
| eligibility | string | required | PASS / FAIL / UNKNOWN |
| eligibility_reason | string | optional | Explanation |
| skill_match | float | 0.0–1.0 | Skill overlap score |
| role_match | float | 0.0–1.0 | Role relevance score |
| location_match | float | 0.0–1.0 | Location preference fit |
| preference_match | float | 0.0–1.0 | Overall preference fit |
| deadline_risk | string | optional | low / medium / high / expired |
| overall_score | float | 0.0–1.0 | Weighted composite score |
| missing_skills | list[string] | optional | Skills student lacks |
| explanation | text | optional | Human-readable summary |
| calculated_at | datetime | auto | When computed |

---

### Application

A student's application to an opportunity.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| application_id | UUID | PK | Unique application ID |
| student_id | UUID | FK → Student | Applicant |
| opportunity_id | UUID | FK → Opportunity | Target opportunity |
| status | string | required | draft / pending_approval / approved / submitted / interview / selected / rejected / withdrawn |
| resume_version | integer | optional | Which resume version used |
| draft_application | JSON | optional | Draft application content |
| approval_state | string | optional | pending / approved / rejected |
| approved_by | string | optional | Who approved |
| approved_at | datetime | optional | When approved |
| submission_reference | string | optional | External submission ID |
| created_at | datetime | auto | When created |
| updated_at | datetime | auto | Last update |

---

### Progress

Milestones during an active internship.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique progress ID |
| application_id | UUID | FK → Application | Related application |
| milestone | string | required | Milestone name |
| status | string | required | not_started / in_progress / completed |
| start_date | date | optional | Milestone start |
| end_date | date | optional | Milestone end |
| notes | text | optional | Description / notes |
| evidence | JSON | optional | Supporting evidence |

---

### Evaluation

Final evaluation for a completed internship.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique evaluation ID |
| application_id | UUID | FK → Application, unique | Related application |
| mentor_feedback | text | optional | Mentor's feedback |
| company_feedback | text | optional | Company's feedback |
| rubric | JSON | optional | Evaluation rubric used |
| draft_score | float | optional | AI-generated draft score |
| final_score | float | optional | Human-approved final score |
| final_grade | string | optional | Letter grade |
| approved_by | string | optional | Who approved final grade |
| evaluated_at | datetime | optional | When finalized |

---

### AuditEvent

Immutable record of every meaningful system action.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| event_id | UUID | PK | Unique event ID |
| trace_id | string | indexed | Workflow trace ID |
| timestamp | datetime | auto | When the event occurred |
| actor_type | string | required | "agent" / "tool" / "user" / "system" |
| actor_id | string | optional | Who performed the action |
| agent | string | optional | Agent name (if actor is agent) |
| action | string | required | Action performed |
| tool | string | optional | Tool name (if tool was called) |
| input_summary | text | optional | Summarized input |
| output_summary | text | optional | Summarized output |
| approval_state | string | optional | If approval was involved |
| status | string | required | success / failure / error |
| error | text | optional | Error details if failed |
| metadata | JSON | optional | Additional context |

---

## Design Notes

1. **UUIDs** — All primary keys use UUID v4 for uniqueness across potential
   future distributed deployments.

2. **JSON fields** — Used for semi-structured data (parsed profiles,
   eligibility requirements, rubrics). SQLite supports JSON natively.

3. **Timestamps** — All entities have creation timestamps. Mutable entities
   also have `updated_at`.

4. **Soft references** — AuditEvent uses string references rather than
   foreign keys to remain decoupled from specific entities.

5. **Migration path** — The repository pattern abstracts all SQL. Moving
   to PostgreSQL requires only changing the connection string and potentially
   updating JSON field types.
