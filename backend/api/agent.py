"""Context-aware Personal Assistant & Conversational Coordinator Endpoint with Shared Memory."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.agents.coordinator import chat_with_assistant, coordinate, new_state
from backend.core.config import get_settings
from backend.models.schemas import CandidatePreference
from backend.repositories.opportunity_repository import OpportunityRepository
from backend.repositories.preference_repository import PreferenceRepository
from backend.repositories.resume_repository import ResumeRepository
from backend.repositories.session_repository import SessionRepository
from backend.skills.memory_manager import MemoryManager

router = APIRouter(prefix="/agent", tags=["agent"])


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    student_id: str = Field(default="demo-student-123")
    resume_id: str | None = None


class MessageResponse(BaseModel):
    session_id: str
    trace_id: str
    action: str
    response: str
    missing_fields: list[str] = Field(default_factory=list)
    preferences: dict | None = None
    opportunities: list[dict] | None = None
    resume_profile: dict | None = None
    agent_trace: list[str] | None = None


@router.post("/messages", response_model=MessageResponse)
async def send_message(request: MessageRequest) -> MessageResponse:
    db_url = get_settings().database_url
    session_repo = SessionRepository(db_url)
    pref_repo = PreferenceRepository(db_url)
    resume_repo = ResumeRepository(db_url)
    opp_repo = OpportunityRepository(db_url)
    memory_manager = MemoryManager()

    # 1. Load or create session state
    state = await session_repo.get(request.session_id) if request.session_id else None
    state = state or new_state(request.session_id)
    state.student_id = request.student_id

    msg_lower = request.message.lower().strip()

    # 2. Load latest resume & opportunities into session memory if not already present
    latest_resume = (
        await resume_repo.get_by_id(request.resume_id)
        if request.resume_id
        else await resume_repo.get_latest_by_student(request.student_id)
    )
    if latest_resume:
        state.resume_profile = latest_resume
        state.resume_id = latest_resume.get("resume_id")
        if latest_resume.get("skills"):
            state.skills = latest_resume["skills"]

    if not state.opportunities:
        stored_matches = await opp_repo.get_matches_for_student(request.student_id)
        if stored_matches:
            state.opportunities = stored_matches

    # 3. Exact command handlers (preserves backward compatibility with unit tests)
    if msg_lower in ["list my skills", "what are my skills", "show my skills"]:
        if latest_resume and latest_resume.get("skills"):
            display_skills = latest_resume.get("skills_display") or latest_resume["skills"]
            skills_list = "\n".join([f"- {s}" for s in display_skills])
            return MessageResponse(
                session_id=state.session_id,
                trace_id=state.trace_id,
                action="FINISH",
                response=f"Here are your skills:\n**Verified Skills**\n{skills_list}",
                missing_fields=[],
                preferences=None,
                opportunities=state.opportunities or None,
                resume_profile=state.resume_profile or None,
            )
        return MessageResponse(
            session_id=state.session_id,
            trace_id=state.trace_id,
            action="FINISH",
            response="You haven't uploaded a resume yet, so I don't have any skills on file for you.",
            missing_fields=[],
            preferences=None,
            opportunities=None,
        )

    if msg_lower in ["show my profile", "my profile", "who am i"]:
        existing_pref = await pref_repo.get_by_student_id(request.student_id)
        if existing_pref:
            pref_dict = existing_pref.model_dump(
                include={"target_roles", "locations", "work_modes", "minimum_stipend"}
            )
            extra_resume_info = ""
            if latest_resume and latest_resume.get("name"):
                extra_resume_info = (
                    f"\n\n**Resume Profile:** {latest_resume.get('name')} | "
                    f"**Skills:** {len(latest_resume.get('skills', []))} | "
                    f"**Inferred Roles:** {', '.join(latest_resume.get('inferred_roles', [])[:4])}"
                )
            return MessageResponse(
                session_id=state.session_id,
                trace_id=state.trace_id,
                action="FINISH",
                response=f"Here is your current profile preferences:\n```json\n{pref_dict}\n```{extra_resume_info}",
                missing_fields=[],
                preferences=pref_dict,
                opportunities=state.opportunities or None,
                resume_profile=state.resume_profile or None,
            )
        if latest_resume:
            return MessageResponse(
                session_id=state.session_id,
                trace_id=state.trace_id,
                action="FINISH",
                response=(
                    f"**Candidate:** {latest_resume.get('name', 'Candidate')}\n"
                    f"**CGPA:** {latest_resume.get('cgpa', 'N/A')}\n"
                    f"**Skills ({len(latest_resume.get('skills', []))}):** {', '.join((latest_resume.get('skills_display') or latest_resume.get('skills', []))[:15])}\n"
                    f"**Target Roles:** {', '.join(latest_resume.get('inferred_roles', []))}"
                ),
                missing_fields=[],
                preferences=None,
                opportunities=state.opportunities or None,
                resume_profile=latest_resume,
            )
        return MessageResponse(
            session_id=state.session_id,
            trace_id=state.trace_id,
            action="FINISH",
            response="I don't have any profile preferences saved for you yet.",
            missing_fields=[],
            preferences=None,
            opportunities=None,
        )

    # 4. Long-Term Memory Phase: Extract & Merge Preferences
    existing_pref = await pref_repo.get_by_student_id(request.student_id)
    if not existing_pref:
        existing_pref = CandidatePreference(student_id=request.student_id)

    pref_keywords = [
        "want", "prefer", "looking for", "need", "require",
        "internship", "role", "job", "in ", "at ", "remote", "hybrid", "stipend",
    ]
    if len(msg_lower) > 10 and any(k in msg_lower for k in pref_keywords):
        try:
            extraction = await memory_manager.extract_preferences(request.message)
            updated_pref = memory_manager.merge_preferences(existing_pref, extraction)
            await pref_repo.save(updated_pref)
        except Exception:
            updated_pref = existing_pref
    else:
        updated_pref = existing_pref

    if updated_pref.target_roles:
        state.target_role = state.target_role or updated_pref.target_roles[0]
    if updated_pref.locations:
        state.location = state.location or updated_pref.locations[0]
    if updated_pref.minimum_stipend:
        state.minimum_stipend = state.minimum_stipend or updated_pref.minimum_stipend

    pref_dict = updated_pref.model_dump(
        include={"target_roles", "locations", "work_modes", "minimum_stipend"}
    )

    # 5. Route to Context-Aware Personal Assistant if resume or opportunities exist,
    #    or if user asks positional/comparative questions ("1st one", "2nd one", "pays well", "stipend", "full stack")
    assistant_triggers = [
        "1st", "2nd", "3rd", "4th", "5th", "first", "second", "third", "fourth", "fifth",
        "#1", "#2", "#3", "#4", "#5", "stipend", "pay", "pays", "salary", "full stack",
        "fullstack", "full-stack", "backend", "frontend", "missing", "compare", "best",
        "which one", "why", "project", "eligible", "match", "explain", "remote",
    ]
    use_assistant = bool(
        state.opportunities
        or state.resume_profile
        or any(t in msg_lower for t in assistant_triggers)
    )

    if use_assistant:
        assistant_res = await chat_with_assistant(
            message=request.message,
            state=state,
            resume_id=request.resume_id or state.resume_id,
            student_id=request.student_id,
        )
        updated_state = assistant_res["state"]
        await session_repo.save(updated_state)
        await session_repo.audit(
            updated_state.trace_id,
            "assistant_response",
            {"action": assistant_res["action"], "opportunities_count": len(updated_state.opportunities)},
        )
        return MessageResponse(
            session_id=updated_state.session_id,
            trace_id=updated_state.trace_id,
            action=assistant_res["action"],
            response=assistant_res["response"],
            missing_fields=assistant_res.get("missing_fields", []),
            preferences=pref_dict,
            opportunities=assistant_res.get("opportunities") or updated_state.opportunities,
            resume_profile=assistant_res.get("resume_profile") or updated_state.resume_profile,
            agent_trace=assistant_res.get("agent_trace") or updated_state.agent_trace,
        )

    # 6. Fallback to standard Coordinator when no resume is uploaded yet
    result = await coordinate(request.message, state)
    await session_repo.save(result.state)
    await session_repo.audit(
        result.state.trace_id,
        "coordinator_decision",
        {"action": result.action, "missing_fields": result.missing_fields},
    )

    return MessageResponse(
        session_id=result.state.session_id,
        trace_id=result.state.trace_id,
        action=result.action,
        response=result.response,
        missing_fields=result.missing_fields,
        preferences=pref_dict,
        opportunities=result.opportunities,
        resume_profile=result.state.resume_profile or None,
        agent_trace=result.state.agent_trace or None,
    )