"""Lab 1 & 4 conversational coordinator endpoint with Long-Term Memory."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.agents.coordinator import coordinate, new_state
from backend.core.config import get_settings
from backend.repositories.session_repository import SessionRepository
from backend.repositories.preference_repository import PreferenceRepository
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


@router.post("/messages", response_model=MessageResponse)
async def send_message(request: MessageRequest) -> MessageResponse:
    db_url = get_settings().database_url
    session_repo = SessionRepository(db_url)
    pref_repo = PreferenceRepository(db_url)
    memory_manager = MemoryManager()
    
    # Load session state
    state = await session_repo.get(request.session_id) if request.session_id else None
    state = state or new_state(request.session_id)
    
    # Memory Phase (Lab 4): Load, Extract, Merge, Save Preferences
    existing_pref = await pref_repo.get_by_student_id(request.student_id)
    if not existing_pref:
        existing_pref = CandidatePreference(student_id=request.student_id)
        
    extraction = await memory_manager.extract_preferences(request.message)
    updated_pref = memory_manager.merge_preferences(existing_pref, extraction)
    await pref_repo.save(updated_pref)
    
    # Sync preferences back to state so the coordinator doesn't ask for things we already know
    if updated_pref.target_roles:
        state.target_role = state.target_role or updated_pref.target_roles[0]
    if updated_pref.locations:
        state.location = state.location or updated_pref.locations[0]
    if updated_pref.minimum_stipend:
        state.minimum_stipend = state.minimum_stipend or updated_pref.minimum_stipend
    
    # Coordinator Phase (Lab 1)
    result = coordinate(request.message, state)
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
        preferences=pref_dict
    )

