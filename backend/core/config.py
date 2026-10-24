"""
InternPilot — Application Configuration

Loads settings from environment variables with support for Groq, OpenRouter,
Adzuna Live API, Tavily Search API, and MCP Connectors.
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Force .env file to override OS environment variables
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ---- Application ----
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    # ---- LLM Brain (Groq / OpenRouter / Gemini / Ollama) ----
    llm_provider: str = Field(default="groq", description="groq, openrouter, gemini, or ollama")
    llm_model: str = Field(default="llama-3.3-70b-versatile", description="Active LLM model name")
    groq_api_key: str = Field(default="", description="Groq API Key")
    openrouter_api_key: str = Field(default="", description="OpenRouter API Key")
    openrouter_model: str = Field(
        default="meta-llama/llama-3.3-70b-instruct",
        description="Default OpenRouter model",
    )
    gemini_api_key: str = Field(default="", description="Google Gemini API Key")
    llm_base_url: str = Field(default="http://localhost:11434")
    llm_timeout: float = Field(default=25.0)

    # ---- Database ----
    database_url: str = Field(
        default=f"sqlite:///{DATA_DIR / 'internpilot.db'}",
        description="Database connection URL",
    )

    # ---- Opportunity Providers & MCP ----
    opportunity_provider: str = Field(
        default="adzuna", description="adzuna, tavily, or mock (for unit tests only)"
    )
    adzuna_app_id: str = Field(default="")
    adzuna_app_key: str = Field(default="")
    tavily_api_key: str = Field(default="")
    mcp_enabled: bool = Field(default=True)

    # ---- Frontend ----
    frontend_port: int = Field(default=5173)
    frontend_url: str = Field(default="http://localhost:5173")

    # ---- Observability ----
    log_level: str = Field(default="INFO")

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()