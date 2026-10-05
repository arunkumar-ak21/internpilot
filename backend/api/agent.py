"""Lab 1 conversational coordinator endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.agents.coordinator import coordinate, new_state
from backend.core.config import get_settings
from backend.repositories.session_repository import SessionRepository

router = APIRouter(prefix="/agent", tags=["agent"])


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class MessageResponse(BaseModel):
    session_id: str
    trace_id: str
    action: str
    response: str
    missing_fields: list[str]


@router.post("/messages", response_model=MessageResponse)
async def send_message(request: MessageRequest) -> MessageResponse:
    repository = SessionRepository(get_settings().database_url)
    state = await repository.get(request.session_id) if request.session_id else None
    result = coordinate(request.message, state or new_state(request.session_id))
    await repository.save(result.state)
    await repository.audit(result.state.trace_id, "coordinator_decision", {"action": result.action, "missing_fields": result.missing_fields})
    return MessageResponse(session_id=result.state.session_id, trace_id=result.state.trace_id, action=result.action, response=result.response, missing_fields=result.missing_fields)
