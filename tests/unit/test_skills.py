"""Unit tests for the Internship Research Skill."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from backend.skills.internship_research import InternshipResearchSkill, ResearchResult
from backend.models.schemas import Opportunity


@pytest.mark.asyncio
async def test_internship_research_skill():
    """Test the research skill extracts structured info correctly."""
    
    mock_result = ResearchResult(
        company="Tech Corp",
        role="Data Scientist Intern",
        location="Remote",
        work_mode="Remote",
        stipend="$5000/month",
        duration="3 months",
        deadline="2026-12-01",
        eligibility=["Must be a student"],
        skills=["Python", "Machine Learning"],
        application_process="Apply on website",
        company_context="Tech Corp is a fast-growing startup.",
        important_observations=["High stipend, remote friendly"],
        evidence=["From description: 'Work from anywhere'"],
        confidence=0.95
    )
    
    skill = InternshipResearchSkill()
    
    # Replace the entire LangChain pipeline with a mock to bypass internals
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=mock_result)
    skill.chain = mock_chain
    
    opportunity = Opportunity(
        company="Tech Corp",
        role="Data Scientist Intern",
        source="mock",
        description="We are looking for a Data Scientist Intern. Must be a student. Skills: Python, Machine Learning. Work from anywhere. $5000/month."
    )
    
    result = await skill.execute(opportunity)
    
    assert isinstance(result, ResearchResult)
    assert result.company == "Tech Corp"
    assert result.skills == ["Python", "Machine Learning"]
    assert result.confidence == 0.95
    
    mock_chain.ainvoke.assert_called_once()
    call_args = mock_chain.ainvoke.call_args[0][0]
    assert call_args["company"] == "Tech Corp"
    assert call_args["role"] == "Data Scientist Intern"


@pytest.mark.asyncio
async def test_internship_research_skill_fallback():
    """Test the research skill handles LLM failures gracefully via fallback."""
    
    skill = InternshipResearchSkill()
    
    # Replace the entire LangChain pipeline with a mock
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(side_effect=RuntimeError("LLM connection refused"))
    skill.chain = mock_chain
    
    opportunity = Opportunity(
        company="Failing LLM Corp",
        role="Intern",
        source="mock"
    )
    
    result = await skill.execute(opportunity)
    
    assert isinstance(result, ResearchResult)
    assert result.company == "Failing LLM Corp"
    assert result.confidence == 0.0
    assert len(result.important_observations) > 0
    assert "LLM connection refused" in result.important_observations[0]
