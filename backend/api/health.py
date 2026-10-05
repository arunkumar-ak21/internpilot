"""Non-sensitive service health endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.config import get_settings
from backend.core.database import database_is_ready

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    environment: str


class ReadinessResponse(HealthResponse):
    database: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Confirm that the API process is running."""
    settings = get_settings()
    return HealthResponse(status="ok", environment=settings.app_env)


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Confirm that backing services required by this milestone are available."""
    settings = get_settings()
    ready = await database_is_ready()
    return ReadinessResponse(
        status="ok" if ready else "degraded",
        environment=settings.app_env,
        database="ready" if ready else "unavailable",
    )
