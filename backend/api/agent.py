"""Lab 1 & 4 conversational coordinator endpoint with Long-Term Memory."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.agents.coordinator import coordinate, new_state
from backend.core.config import get_settings
from backend.repositories.session_repository import SessionRepository
from backend.repositories.preference_repository import PreferenceRepository
from backend.repositories.resume_repository import ResumeRepository
from backend.skills.memory_manager import MemoryManager
from backend.models.schemas import CandidatePreference

router = APIRouter(prefix="/agent", tags=["agent"])


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    student_id: str = Field(default="demo-student-123")


class MessageResponse(BaseModel):
    session_id: str
    trace_id: str
    action: str
    response: str
    missing_fields: list[str]
    preferences: dict | None = None
    opportunities: list[dict] | None = None


@router.post("/messages", response_model=MessageResponse)
async def send_message(request: MessageRequest) -> MessageResponse:
    db_url = get_settings().database_url
    session_repo = SessionRepository(db_url)
    pref_repo = PreferenceRepository(db_url)
    memory_manager = MemoryManager()
    
    # Load session state
    print("[DEBUG] Loading session state")
    state = await session_repo.get(request.session_id) if request.session_id else None
    state = state or new_state(request.session_id)
    
    msg_lower = request.message.lower().strip()
    
    # 1. Deterministic Action: List Skills
    if msg_lower in ["list my skills", "what are my skills", "show my skills"]:
        resume_repo = ResumeRepository(db_url)
        latest_resume = await resume_repo.get_latest_by_student(request.student_id)
        if latest_resume and "skills" in latest_resume and latest_resume["skills"]:
            skills_list = "\n".join([f"- {s}" for s in latest_resume["skills"]])
            return MessageResponse(
                session_id=state.session_id, trace_id=state.trace_id, action="FINISH",
                response=f"Here are your skills:\n**Verified Skills**\n{skills_list}",
                missing_fields=[], preferences=None, opportunities=None
            )
        return MessageResponse(
            session_id=state.session_id, trace_id=state.trace_id, action="FINISH",
            response="You haven't uploaded a resume yet, so I don't have any skills on file for you.",
            missing_fields=[], preferences=None, opportunities=None
        )

    # 2. Deterministic Action: Show Profile
    if msg_lower in ["show my profile", "my profile", "who am i"]:
        existing_pref = await pref_repo.get_by_student_id(request.student_id)
        if existing_pref:
            pref_dict = existing_pref.model_dump(include={'target_roles', 'locations', 'work_modes', 'minimum_stipend'})
            return MessageResponse(
                session_id=state.session_id, trace_id=state.trace_id, action="FINISH",
                response=f"Here is your current profile preferences:\n```json\n{pref_dict}\n```",
                missing_fields=[], preferences=pref_dict, opportunities=None
            )
        return MessageResponse(
            session_id=state.session_id, trace_id=state.trace_id, action="FINISH",
            response="I don't have any profile preferences saved for you yet.",
            missing_fields=[], preferences=None, opportunities=None
        )

    # Memory Phase (Lab 4): Load, Extract, Merge, Save Preferences
    print("[DEBUG] Getting preferences from DB")
    existing_pref = await pref_repo.get_by_student_id(request.student_id)
    if not existing_pref:
        existing_pref = CandidatePreference(student_id=request.student_id)
        
    # Only run LLM extraction if message is long enough or contains preference keywords
    pref_keywords = ["want", "prefer", "looking for", "need", "require", "internship", "role", "job", "in ", "at "]
    if len(msg_lower) > 10 and any(k in msg_lower for k in pref_keywords):
        print("[DEBUG] Extracting preferences via LLM")
        try:
            extraction = await memory_manager.extract_preferences(request.message)
            print("[DEBUG] Merging preferences")
            updated_pref = memory_manager.merge_preferences(existing_pref, extraction)
            print("[DEBUG] Saving preferences to DB")
            await pref_repo.save(updated_pref)
        except Exception as e:
            print(f"[DEBUG] LLM extraction failed, falling back to existing preferences: {e}")
            updated_pref = existing_pref
    else:
        updated_pref = existing_pref
    
    # Sync preferences back to state so the coordinator doesn't ask for things we already know
    print("[DEBUG] Syncing preferences")
    if updated_pref.target_roles:
        state.target_role = state.target_role or updated_pref.target_roles[0]
    if updated_pref.locations:
        state.location = state.location or updated_pref.locations[0]
    if updated_pref.minimum_stipend:
        state.minimum_stipend = state.minimum_stipend or updated_pref.minimum_stipend
        
    # Fetch latest resume skills
    print("[DEBUG] Fetching skills")
    resume_repo = ResumeRepository(db_url)
    latest_resume = await resume_repo.get_latest_by_student(request.student_id)
    if latest_resume and "skills" in latest_resume:
        state.skills = latest_resume["skills"]
        
    # Coordinator Phase (Lab 1)
    print("[DEBUG] Calling coordinate()")
    result = await coordinate(request.message, state)
    print("[DEBUG] coordinate() finished")
    await session_repo.save(result.state)
    await session_repo.audit(result.state.trace_id, "coordinator_decision", {"action": result.action, "missing_fields": result.missing_fields})
    
    # Return response including preferences
    pref_dict = updated_pref.model_dump(include={'target_roles', 'locations', 'work_modes', 'minimum_stipend'})
    
    return MessageResponse(
        session_id=result.state.session_id, 
        trace_id=result.state.trace_id, 
        action=result.action, 
        response=result.response, 
        missing_fields=result.missing_fields,
        preferences=pref_dict,
        opportunities=result.opportunities
    )

