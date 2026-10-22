"""Coordinator Agent — Orchestrates the multi-agent pipeline."""

from __future__ import annotations
import uuid
import asyncio
import re
from dataclasses import asdict, dataclass, field

from backend.agents.discovery_agent import run_discovery
from backend.agents.eligibility_agent import run_eligibility
from backend.repositories.resume_repository import ResumeRepository
from backend.core.config import get_settings


# ==========================================
# State & Result Types
# ==========================================

@dataclass
class ConversationState:
    """The persistent application state (saved to DB)."""
    session_id: str
    trace_id: str
    target_role: str | None = None
    location: str | None = None
    minimum_stipend: int | None = None
    skills: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    opportunities: list[dict] = field(default_factory=list)


@dataclass
class CoordinatorResult:
    state: ConversationState
    action: str
    response: str
    missing_fields: list[str]
    opportunities: list[dict] = field(default_factory=list)

    def __await__(self):
        async def _identity():
            return self
        return _identity().__await__()


@dataclass
class PipelineResult:
    """Full result of the one-shot pipeline."""
    resume_profile: dict
    agent_trace: list[str]
    recommendations: list[dict]
    status: str  # completed, partial, failed


# ==========================================
# One-Shot Pipeline
# ==========================================

async def run_pipeline(resume_id: str | None = None, student_id: str | None = None,
                       location: str | None = None,
                       candidate_profile: dict | None = None) -> PipelineResult:
    """
    Execute the full Coordinator -> Discovery -> Eligibility pipeline.
    No human approval gate. Runs to completion and returns results.
    """
    trace = []
    profile = candidate_profile or {}

    # Step 1: Load the candidate profile
    trace.append("Coordinator: Starting pipeline execution...")

    if not profile:
        repo = ResumeRepository(get_settings().database_url)
        if resume_id:
            profile = await repo.get_by_id(resume_id) or {}
        elif student_id:
            profile = await repo.get_latest_by_student(student_id) or {}

    if not profile or not profile.get("skills"):
        trace.append("Coordinator: No candidate profile found or no skills extracted.")
        return PipelineResult(
            resume_profile=profile,
            agent_trace=trace,
            recommendations=[],
            status="failed",
        )

    skills = profile.get("skills", [])
    inferred_roles = profile.get("inferred_roles", [])

    trace.append(f"Coordinator: Loaded candidate profile with {len(skills)} skills and {len(inferred_roles)} inferred target roles.")
    trace.append(f"Coordinator: Top skills = {skills[:8]}")
    trace.append(f"Coordinator: Target roles = {inferred_roles}")
    trace.append("Coordinator: Delegating to Discovery Agent...")

    # Step 2: Run Discovery Agent
    try:
        discovery_result = await run_discovery(
            skills=skills,
            inferred_roles=inferred_roles,
            location=location,
            max_results=15,
        )
        trace.extend(discovery_result["trace"])
        opportunities = discovery_result["opportunities"]
    except Exception as e:
        trace.append(f"Coordinator: Discovery Agent failed: {e}")
        opportunities = []

    if not opportunities:
        trace.append("Coordinator: No opportunities found. Pipeline complete with no results.")
        return PipelineResult(
            resume_profile=profile,
            agent_trace=trace,
            recommendations=[],
            status="no_results",
        )

    trace.append(f"Coordinator: Received {len(opportunities)} opportunities. Delegating to Eligibility Agent...")

    # Step 3: Run Eligibility Agent
    try:
        eligibility_result = await run_eligibility(
            candidate_profile=profile,
            opportunities=opportunities,
        )
        trace.extend(eligibility_result["trace"])
        recommendations = eligibility_result["recommendations"]
    except Exception as e:
        trace.append(f"Coordinator: Eligibility Agent failed: {e}")
        recommendations = opportunities  # Return unscored if eligibility fails

    status = "completed" if recommendations else "no_results"
    trace.append(f"Coordinator: Pipeline complete. Status = {status}. Returning {len(recommendations)} ranked recommendations.")

    return PipelineResult(
        resume_profile=profile,
        agent_trace=trace,
        recommendations=recommendations,
        status=status,
    )


# ==========================================
# Conversational Chat Entrypoint
# ==========================================

def new_state(session_id: str | None = None) -> ConversationState:
    return ConversationState(session_id=session_id or str(uuid.uuid4()), trace_id=str(uuid.uuid4()))


def _role(message: str) -> str | None:
    lowered = message.lower()
    for phrase in ("ai/ml", "ai", "machine learning", "data science", "software", "frontend", "backend", "full-stack", "full stack"):
        if phrase in lowered:
            return "AI/ML" if phrase in {"ai", "ai/ml", "machine learning"} else phrase.title()
    return None


def _location(message: str) -> str | None:
    lowered = message.lower()
    if "remote" in lowered:
        return "Remote"
    match = re.search(r"\bin\s+([A-Za-z ]+?)(?:\s+or\s+remote|[,.]|$)", message, re.I)
    return match.group(1).strip().title() if match else None


def _stipend(message: str) -> int | None:
    match = re.search(r"(?:₹|rs\.?\s*)(\d[\d,]*)", message, re.I)
    return int(match.group(1).replace(",", "")) if match else None


def coordinate(message: str, state: ConversationState) -> CoordinatorResult:
    """Interpret a request and decide whether to clarify, search, or answer."""
    state.messages.append(message)
    state.target_role = _role(message) or state.target_role
    state.location = _location(message) or state.location
    state.minimum_stipend = _stipend(message) or state.minimum_stipend

    # Missing critical search parameters
    missing = []
    if not state.target_role and not state.skills:
        missing.append("target role")
    if not state.location:
        missing.append("location")

    if missing:
        return CoordinatorResult(
            state=state,
            action="clarify",
            response=f"I can help find internships. What {' and '.join(missing)} do you prefer?",
            missing_fields=missing,
            opportunities=state.opportunities,
        )

    role_desc = state.target_role or "matching"
    return CoordinatorResult(
        state=state,
        action="search",
        response=f"I have your search intent: {role_desc} internships in {state.location}. I will now search configured sources.",
        missing_fields=[],
        opportunities=state.opportunities,
    )


def serialize_state(state: ConversationState) -> dict:
    return asdict(state)


def deserialize_state(payload: dict) -> ConversationState:
    return ConversationState(**payload)
