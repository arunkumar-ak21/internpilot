"""The Lab 1 coordinator: explicit state, clarification, and routing."""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Literal


@dataclass
class ConversationState:
    session_id: str
    trace_id: str
    target_role: str | None = None
    location: str | None = None
    minimum_stipend: int | None = None
    messages: list[str] = field(default_factory=list)


@dataclass
class CoordinatorResult:
    state: ConversationState
    action: Literal["clarify", "search"]
    response: str
    missing_fields: list[str]


def new_state(session_id: str | None = None) -> ConversationState:
    return ConversationState(session_id=session_id or str(uuid.uuid4()), trace_id=str(uuid.uuid4()))


def _role(message: str) -> str | None:
    lowered = message.lower()
    for phrase in ("ai/ml", "ai", "machine learning", "data science", "software", "frontend"):
        if phrase in lowered:
            return "AI/ML" if phrase in {"ai", "ai/ml", "machine learning"} else phrase.title()
    return None


def _location(message: str) -> str | None:
    lowered = message.lower()
    if "remote" in lowered:
        return "remote"
    match = re.search(r"\bin\s+([A-Za-z ]+?)(?:\s+or\s+remote|[,.]|$)", message, re.I)
    return match.group(1).strip().title() if match else None


def _stipend(message: str) -> int | None:
    match = re.search(r"(?:₹|rs\.?\s*)(\d[\d,]*)", message, re.I)
    return int(match.group(1).replace(",", "")) if match else None


def coordinate(message: str, state: ConversationState) -> CoordinatorResult:
    """Interpret a request and decide whether to clarify or begin discovery."""
    state.messages.append(message)
    state.target_role = _role(message) or state.target_role
    state.location = _location(message) or state.location
    state.minimum_stipend = _stipend(message) or state.minimum_stipend
    missing = [name for name, value in (("target role", state.target_role), ("location", state.location)) if not value]
    if missing:
        return CoordinatorResult(
            state=state,
            action="clarify",
            response=f"I can help find internships. What {' and '.join(missing)} do you prefer?",
            missing_fields=missing,
        )
    return CoordinatorResult(
        state=state,
        action="search",
        response=f"I have your search intent: {state.target_role} internships in {state.location}. I will now search configured sources.",
        missing_fields=[],
    )


def serialize_state(state: ConversationState) -> dict:
    return asdict(state)


def deserialize_state(payload: dict) -> ConversationState:
    return ConversationState(**payload)
