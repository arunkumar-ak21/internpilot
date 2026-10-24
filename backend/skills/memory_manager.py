"""
Memory & Retrieval Skill

Provides logic to extract and persist student preferences (Long-Term Memory)
from chat history, and retrieve them to augment the conversational context.
Includes both LLM extraction and fast deterministic extraction.
"""

from __future__ import annotations

import asyncio
import re
from typing import List, Optional

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.core.config import get_settings
from backend.models.schemas import CandidatePreference, WorkMode


class PreferenceExtraction(BaseModel):
    """Schema for extracting preference updates from a message."""
    target_roles: Optional[List[str]] = Field(None, description="Roles the student is looking for (e.g. Data Scientist)")
    locations: Optional[List[str]] = Field(None, description="Locations the student wants to work in")
    work_modes: Optional[List[str]] = Field(None, description="Remote, onsite, or hybrid")
    minimum_stipend: Optional[int] = Field(None, description="Minimum acceptable stipend amount in raw numbers (e.g., 5000)")


def extract_preferences_deterministic(message: str) -> PreferenceExtraction:
    """Fast deterministic preference extraction when LLM is unavailable or times out."""
    lower = message.lower()

    # Extract work modes
    modes = []
    for mode in ("remote", "hybrid", "onsite", "on-site"):
        if mode in lower:
            modes.append("onsite" if mode == "on-site" else mode)

    # Extract locations
    known_cities = [
        "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "chennai",
        "delhi", "noida", "gurgaon", "gurugram", "kolkata", "belagavi", "hubballi", "india",
    ]
    locations = [c.title() for c in known_cities if re.search(rf"\b{c}\b", lower)]

    # Extract roles
    role_map = {
        "full stack": "Full-Stack Developer",
        "full-stack": "Full-Stack Developer",
        "fullstack": "Full-Stack Developer",
        "backend": "Backend Engineer",
        "frontend": "Frontend Developer",
        "ai/ml": "AI/ML Engineer",
        "machine learning": "Machine Learning Engineer",
        "deep learning": "Deep Learning Engineer",
        "data science": "Data Scientist",
        "data scientist": "Data Scientist",
        "genai": "Generative AI Engineer",
        "generative ai": "Generative AI Engineer",
        "agentic": "Agentic AI Engineer",
        "computer vision": "Computer Vision Engineer",
        "devops": "DevOps Engineer",
        "cloud": "Cloud Engineer",
    }
    roles = []
    for k, canonical in role_map.items():
        if k in lower and canonical not in roles:
            roles.append(canonical)

    # Extract minimum stipend
    min_stipend = None
    stipend_match = re.search(r"(?:₹|rs\.?|inr|stipend|above|minimum|at least)\s*(\d{2,3}(?:,\d{3})+|\d+k|\d{4,6})", lower)
    if stipend_match:
        raw = stipend_match.group(1).replace(",", "").strip()
        if raw.endswith("k"):
            min_stipend = int(raw[:-1]) * 1000
        elif raw.isdigit():
            min_stipend = int(raw)

    return PreferenceExtraction(
        target_roles=roles or None,
        locations=locations or None,
        work_modes=modes or None,
        minimum_stipend=min_stipend,
    )


class MemoryManager:
    """Manages extraction of long-term memory (preferences) from conversation."""

    def __init__(self, llm=None):
        settings = get_settings()
        if llm is not None:
            self.llm = llm
        elif settings.llm_provider == "groq" and settings.groq_api_key:
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(
                model_name=settings.llm_model,
                temperature=0.0,
                groq_api_key=settings.groq_api_key,
                max_retries=1,
                timeout=8.0,
            )
        elif settings.llm_provider == "gemini" and settings.gemini_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                temperature=0.0,
                google_api_key=settings.gemini_api_key,
            )
        else:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(
                model=settings.llm_model,
                base_url=settings.llm_base_url,
                temperature=0.0,
            )

        self.parser = PydanticOutputParser(pydantic_object=PreferenceExtraction)

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an intelligent memory manager. Your task is to extract internship preferences from a student's message and return them as structured data.\n\n{format_instructions}",
            ),
            (
                "user",
                "Extract any explicit internship preferences from the following message.\nMessage: {message}",
            ),
        ])

        self.chain = self.prompt | self.llm | self.parser

    async def extract_preferences(self, message: str) -> PreferenceExtraction:
        """Analyze a single message for new preferences with deterministic fallback."""
        try:
            res = await asyncio.wait_for(
                self.chain.ainvoke({
                    "message": message,
                    "format_instructions": self.parser.get_format_instructions(),
                }),
                timeout=8.0,
            )
            return res
        except Exception:
            return extract_preferences_deterministic(message)

    def merge_preferences(
        self, existing: CandidatePreference, extraction: PreferenceExtraction
    ) -> CandidatePreference:
        """Merge newly extracted preferences into the existing long-term memory."""
        if extraction.target_roles:
            current_roles = existing.target_roles or []
            existing.target_roles = list(dict.fromkeys(current_roles + extraction.target_roles))

        if extraction.locations:
            current_locations = existing.locations or []
            existing.locations = list(dict.fromkeys(current_locations + extraction.locations))

        if extraction.work_modes:
            current_modes = existing.work_modes or []
            new_modes = []
            for mode in extraction.work_modes:
                mode_clean = mode.lower().strip()
                if mode_clean in [m.value for m in WorkMode]:
                    new_modes.append(WorkMode(mode_clean))
            existing.work_modes = list(dict.fromkeys(current_modes + new_modes))

        if extraction.minimum_stipend:
            if not existing.minimum_stipend or extraction.minimum_stipend > existing.minimum_stipend:
                existing.minimum_stipend = extraction.minimum_stipend

        return existing