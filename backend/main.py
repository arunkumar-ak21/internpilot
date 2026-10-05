"""FastAPI application entry point for InternPilot."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health import router as health_router
from backend.core.config import get_settings
from backend.core.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize infrastructure before serving requests."""
    await initialize_database()
    yield


def create_app() -> FastAPI:
    """Build the application without exposing secrets or provider internals."""
    settings = get_settings()
    app = FastAPI(
        title="InternPilot API",
        version="0.1.0",
        description="Agentic internship discovery platform (foundation API).",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Trace-ID"],
    )
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
