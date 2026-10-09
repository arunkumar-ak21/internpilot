"""
Internship Research Skill

A reusable capability package (skill) that accepts an opportunity and returns
a structured research result synthesizing company context, eligibility, skills,
and application processes.
"""

from typing import Optional, List
import asyncio
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from backend.models.schemas import Opportunity
from backend.core.config import get_settings


class ResearchResult(BaseModel):
    """Structured output for the Internship Research Skill."""
    company: str = Field(description="Company name")
    role: str = Field(description="Role title")
    location: Optional[str] = Field(None, description="Location of the internship")
    work_mode: Optional[str] = Field(None, description="Remote, onsite, or hybrid")
    stipend: Optional[str] = Field(None, description="Stipend or salary details")
    duration: Optional[str] = Field(None, description="Duration of the internship")
    deadline: Optional[str] = Field(None, description="Application deadline")
    eligibility: List[str] = Field(default_factory=list, description="Eligibility requirements")
    skills: List[str] = Field(default_factory=list, description="Required or preferred skills")
    application_process: Optional[str] = Field(None, description="Details on how to apply")
    company_context: Optional[str] = Field(None, description="Background info about the company")
    important_observations: List[str] = Field(default_factory=list, description="Key insights or red flags")
    evidence: List[str] = Field(default_factory=list, description="Source references or quotes backing the research")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the research synthesis (0.0 to 1.0)")


class InternshipResearchSkill:
    """
    Skill for researching and extracting structured insights from an internship opportunity.
    """

    def __init__(self, llm=None):
        settings = get_settings()
        self.llm = llm or ChatOllama(
            model=settings.llm_model, 
            base_url=settings.llm_base_url,
            temperature=0.1 # Low temperature for more deterministic extraction
        )
        self.parser = PydanticOutputParser(pydantic_object=ResearchResult)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert career counselor and research assistant. Your task is to extract, infer, and synthesize structured research data from an internship opportunity listing.\n\n{format_instructions}"),
            ("user", "Analyze the following internship opportunity and provide a structured research result.\n\nTarget Objective: {objective}\n\nOpportunity Data:\nCompany: {company}\nRole: {role}\nLocation: {location}\nDescription:\n{description}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    async def execute(self, opportunity: Opportunity, objective: str = "Extract comprehensive details for a student application.") -> ResearchResult:
        """
        Execute the research skill on a given opportunity.
        """
        # Execute the chain asynchronously
        try:
            result = await asyncio.wait_for(
                self.chain.ainvoke({
                    "company": opportunity.company,
                    "role": opportunity.role,
                    "location": opportunity.location or "Unknown",
                    "description": opportunity.description or "No description provided.",
                    "objective": objective,
                    "format_instructions": self.parser.get_format_instructions()
                }),
                timeout=15.0
            )
            return result
        except Exception as e:
            # Fallback for failing LLMs or missing models (e.g. during testing without local ollama)
            return ResearchResult(
                company=opportunity.company,
                role=opportunity.role,
                location=opportunity.location,
                work_mode=opportunity.work_mode,
                stipend=opportunity.stipend,
                important_observations=[f"Research failed or fallback triggered: {str(e)}"],
                confidence=0.0
            )
