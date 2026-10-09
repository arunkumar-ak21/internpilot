"""
Memory & Retrieval Skill (Lab 4)

Provides logic to extract and persist student preferences (Long-Term Memory)
from chat history, and retrieve them to augment the conversational context.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from backend.models.schemas import CandidatePreference, WorkMode
from backend.core.config import get_settings


class PreferenceExtraction(BaseModel):
    """Schema for extracting preference updates from a message."""
    target_roles: Optional[List[str]] = Field(None, description="Roles the student is looking for (e.g. Data Scientist)")
    locations: Optional[List[str]] = Field(None, description="Locations the student wants to work in")
    work_modes: Optional[List[str]] = Field(None, description="Remote, onsite, or hybrid")
    minimum_stipend: Optional[int] = Field(None, description="Minimum acceptable stipend amount in raw numbers (e.g., 5000)")


class MemoryManager:
    """Manages extraction of long-term memory (preferences) from conversation."""

    def __init__(self, llm=None):
        settings = get_settings()
        if llm:
            self.llm = llm
        elif settings.llm_provider == "groq":
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(model_name=settings.llm_model, temperature=0.0, groq_api_key=settings.groq_api_key, max_retries=1, timeout=10.0)
        elif settings.llm_provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(model=settings.llm_model, temperature=0.0, google_api_key=settings.gemini_api_key)
        else:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(model=settings.llm_model, base_url=settings.llm_base_url, temperature=0.0)
        
        self.parser = PydanticOutputParser(pydantic_object=PreferenceExtraction)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent memory manager. Your task is to extract internship preferences from a student's message and return them as structured data.\n\n{format_instructions}"),
            ("user", "Extract any explicit internship preferences from the following message.\nMessage: {message}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    async def extract_preferences(self, message: str) -> PreferenceExtraction:
        """Analyze a single message for new preferences."""
        try:
            return await self.chain.ainvoke({
                "message": message,
                "format_instructions": self.parser.get_format_instructions()
            })
        except Exception:
            # Fallback to empty extraction if LLM fails
            return PreferenceExtraction()

    def merge_preferences(self, existing: CandidatePreference, extraction: PreferenceExtraction) -> CandidatePreference:
        """Merge newly extracted preferences into the existing long-term memory."""
        # This is a naive merge strategy for Lab 4
        
        if extraction.target_roles:
            current_roles = existing.target_roles or []
            existing.target_roles = list(set(current_roles + extraction.target_roles))
            
        if extraction.locations:
            current_locations = existing.locations or []
            existing.locations = list(set(current_locations + extraction.locations))
            
        if extraction.work_modes:
            current_modes = existing.work_modes or []
            new_modes = []
            for mode in extraction.work_modes:
                mode = mode.lower()
                if mode in [m.value for m in WorkMode]:
                    new_modes.append(WorkMode(mode))
            existing.work_modes = list(set(current_modes + new_modes))
            
        if extraction.minimum_stipend:
            # Update only if the new stipend requirement is higher, or if none existed
            if not existing.minimum_stipend or extraction.minimum_stipend > existing.minimum_stipend:
                existing.minimum_stipend = extraction.minimum_stipend
                
        return existing
