"""
InternPilot — Domain Models

Pydantic models for all core entities. These serve as:
1. API request/response schemas (FastAPI integration)
2. Validation layer for all data
3. Documentation of the data contract

Design notes:
- UUIDs as primary keys for future distribution readiness
- Optional fields where data may be incomplete
- Strict validation via Pydantic v2
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================
# Enums
# =============================================

class EligibilityStatus(str, Enum):
    """Result of an eligibility check."""
    PASS_ = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class DeadlineRisk(str, Enum):
    """How urgent is the deadline."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXPIRED = "expired"


class ApplicationStatus(str, Enum):
    """Lifecycle status of an application."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    INTERVIEW = "interview"
    SELECTED = "selected"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApprovalState(str, Enum):
    """Approval gate status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProgressStatus(str, Enum):
    """Milestone progress status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class WorkflowStatus(str, Enum):
    QUEUED = "queued"
    EXTRACTING_PROFILE = "extracting_profile"
    PROFILE_READY = "profile_ready"
    DISCOVERING = "discovering"
    MATCHING = "matching"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    NO_RESULTS = "no_results"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActorType(str, Enum):
    """Who performed an audited action."""
    AGENT = "agent"
    TOOL = "tool"
    USER = "user"
    SYSTEM = "system"


class SkillProficiency(str, Enum):
    """Skill proficiency level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SkillSource(str, Enum):
    """How a skill was identified."""
    RESUME = "resume"
    MANUAL = "manual"
    INFERRED = "inferred"


class WorkMode(str, Enum):
    """Work arrangement type."""
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


# =============================================
# Student & Profile
# =============================================

class StudentBase(BaseModel):
    """Fields common to student creation and display."""
    name: str = Field(..., min_length=1, max_length=200, description="Full name")
    email: str = Field(..., min_length=5, max_length=254, description="Contact email")
    branch: Optional[str] = Field(None, max_length=100, description="Academic branch")
    degree: Optional[str] = Field(None, max_length=100, description="Degree program")
    graduation_year: Optional[int] = Field(
        None, ge=2000, le=2040, description="Expected graduation year"
    )
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0, description="Current CGPA")


class StudentCreate(StudentBase):
    """Schema for creating a new student."""
    pass


class Student(StudentBase):
    """Full student entity with ID and timestamps."""
    student_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique student identifier",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Account creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update time"
    )

    model_config = {"from_attributes": True}


# =============================================
# Candidate Skills
# =============================================

class CandidateSkillBase(BaseModel):
    """Fields for a candidate skill."""
    skill: str = Field(..., min_length=1, max_length=100, description="Skill name")
    proficiency: Optional[SkillProficiency] = None
    source: SkillSource = Field(..., description="How skill was identified")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class CandidateSkill(CandidateSkillBase):
    """Full candidate skill entity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = Field(..., description="Owner student ID")

    model_config = {"from_attributes": True}


# =============================================
# Candidate Preferences
# =============================================

class CandidatePreferenceBase(BaseModel):
    """Student's internship search preferences."""
    target_roles: Optional[list[str]] = Field(None, description="Desired roles")
    locations: Optional[list[str]] = Field(None, description="Preferred locations")
    work_modes: Optional[list[WorkMode]] = Field(None, description="Work arrangement")
    minimum_stipend: Optional[int] = Field(None, ge=0, description="Min stipend")
    duration_preferences: Optional[str] = Field(None, description="e.g., 3-6 months")
    availability: Optional[str] = Field(None, description="e.g., Jan 2027")
    additional_constraints: Optional[str] = Field(None, description="Free-text")


class CandidatePreference(CandidatePreferenceBase):
    """Full preference entity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = Field(..., description="Owner student ID")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# =============================================
# Resume
# =============================================

class ResumeBase(BaseModel):
    """Fields for a resume upload."""
    file_name: str = Field(..., description="Original filename")


class Resume(ResumeBase):
    """Full resume entity."""
    resume_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = Field(..., description="Owner student ID")
    file_path: str = Field(..., description="Path to stored file")
    version: int = Field(default=1, description="Resume version")
    extracted_text: Optional[str] = Field(None, description="Raw extracted text")
    parsed_profile: Optional[dict] = Field(None, description="Structured parsed data")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# =============================================
# Opportunity
# =============================================

class OpportunityBase(BaseModel):
    """Core opportunity fields."""
    company: str = Field(..., min_length=1, description="Company name")
    role: str = Field(..., min_length=1, description="Role title")
    description: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[WorkMode] = None
    stipend: Optional[str] = None
    duration: Optional[str] = None
    deadline: Optional[date] = None
    eligibility_requirements: Optional[dict] = None
    required_skills: Optional[list[str]] = None
    application_url: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    """Schema for ingesting a new opportunity."""
    source: str = Field(..., description="Provider name")
    source_id: Optional[str] = Field(None, description="ID from the source system")


class Opportunity(OpportunityBase):
    """Full opportunity entity."""
    opportunity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = Field(..., description="Provider name")
    source_id: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    normalized_data: Optional[dict] = None

    model_config = {"from_attributes": True}


# =============================================
# Opportunity Match
# =============================================

class OpportunityMatch(BaseModel):
    """Computed match between a student and an opportunity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    opportunity_id: str
    eligibility: EligibilityStatus = EligibilityStatus.UNKNOWN
    eligibility_reason: Optional[str] = None
    skill_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    role_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    location_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    preference_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    deadline_risk: Optional[DeadlineRisk] = None
    overall_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    missing_skills: Optional[list[str]] = None
    explanation: Optional[str] = None
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# =============================================
# Application
# =============================================

class ApplicationBase(BaseModel):
    """Core application fields."""
    student_id: str
    opportunity_id: str


class Application(ApplicationBase):
    """Full application entity."""
    application_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: ApplicationStatus = ApplicationStatus.DRAFT
    resume_version: Optional[int] = None
    draft_application: Optional[dict] = None
    approval_state: Optional[ApprovalState] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    submission_reference: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# =============================================
# Progress
# =============================================

class Progress(BaseModel):
    """Internship milestone progress."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    application_id: str
    milestone: str = Field(..., min_length=1)
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    evidence: Optional[dict] = None

    model_config = {"from_attributes": True}


# =============================================
# Evaluation
# =============================================

class Evaluation(BaseModel):
    """Final internship evaluation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    application_id: str
    mentor_feedback: Optional[str] = None
    company_feedback: Optional[str] = None
    rubric: Optional[dict] = None
    draft_score: Optional[float] = None
    final_score: Optional[float] = None
    final_grade: Optional[str] = None
    approved_by: Optional[str] = None
    evaluated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# =============================================
# Audit Event
# =============================================

class AuditEvent(BaseModel):
    """Immutable record of a system action."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(..., description="Workflow trace ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor_type: ActorType
    actor_id: Optional[str] = None
    agent: Optional[str] = None
    action: str = Field(..., min_length=1)
    tool: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    approval_state: Optional[ApprovalState] = None
    status: str = Field(..., description="success / failure / error")
    error: Optional[str] = None
    metadata: Optional[dict] = None

    model_config = {"from_attributes": True}


# =============================================
# Agent Workflow
# =============================================

class AgentWorkflow(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    resume_id: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.QUEUED
    current_stage: str = "queued"
    progress_info: Optional[str] = None
    errors: list[str] = Field(default_factory=list)
    opportunities_discovered: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# =============================================
# Provider Outcome
# =============================================

class ProviderOutcome(BaseModel):
    provider_name: str
    attempted: bool
    result_count: int
    status: str = Field(..., description="success / failed / no_results")
    error: Optional[str] = None
