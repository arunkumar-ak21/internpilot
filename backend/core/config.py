"""
InternPilot — Application Configuration

Loads settings from environment variables with sensible defaults
for local development. Uses pydantic-settings for type-safe config.
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


# ---- Paths ----
# Project root is one level up from backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ---- Application ----
    app_env: str = Field(default="development", description="Environment name")
    app_debug: bool = Field(default=True, description="Enable debug mode")
    app_host: str = Field(default="0.0.0.0", description="Server bind host")
    app_port: int = Field(default=8000, description="Server bind port")

    # ---- LLM ----
    llm_provider: str = Field(default="ollama", description="LLM provider name")
    llm_model: str = Field(default="llama3.2", description="LLM model name")
    llm_base_url: str = Field(
        default="http://localhost:11434", description="LLM API base URL"
    )

    # ---- Database ----
    database_url: str = Field(
        default=f"sqlite:///{DATA_DIR / 'internpilot.db'}",
        description="Database connection URL",
    )

    # ---- Frontend ----
    frontend_port: int = Field(default=5173, description="Frontend dev server port")
    frontend_url: str = Field(
        default="http://localhost:5173", description="Frontend URL for CORS"
    )

    # ---- Observability ----
    log_level: str = Field(default="INFO", description="Application log level")

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings (singleton)."""
    return Settings()
