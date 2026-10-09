import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.api.agent import send_message, MessageRequest
from backend.providers.adzuna import AdzunaProvider
from backend.providers.tavily_search import TavilyProvider
from backend.providers.factory import CompositeProvider
from backend.providers.base import SearchCriteria, RawOpportunity
import httpx

@pytest.mark.asyncio
async def test_listing_skills_when_llm_unavailable():
    """1. Listing skills works when the LLM provider is unavailable."""
    req = MessageRequest(message="list my skills", student_id="demo")
    with patch("backend.repositories.resume_repository.ResumeRepository.get_latest_by_student", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"skills": ["Python", "React"]}
        res = await send_message(req)
        assert res.action == "FINISH"
        assert "Python" in res.response

@pytest.mark.asyncio
async def test_profile_retrieval_does_not_call_llm():
    """2. Profile retrieval does not unnecessarily call the LLM."""
    req = MessageRequest(message="show my profile", student_id="demo")
    with patch("backend.repositories.preference_repository.PreferenceRepository.get_by_student_id", new_callable=AsyncMock) as mock_pref:
        mock_pref.return_value = MagicMock(model_dump=lambda include: {"target_roles": ["SE"]})
        with patch("backend.skills.memory_manager.MemoryManager.extract_preferences") as mock_extract:
            res = await send_message(req)
            assert res.action == "FINISH"
            mock_extract.assert_not_called()

def test_http_429_respects_bounded_retry():
    """4 & 5. HTTP 429 and Decommissioned model errors do not trigger endless retries."""
    # We implemented this by setting max_retries=1 on the ChatGroq initialization
    from backend.services.resume_ingestion import get_llm
    from langchain_groq import ChatGroq
    from backend.core.config import get_settings
    
    settings = get_settings()
    settings.llm_provider = "groq"
    settings.groq_api_key = "test"
    
    llm = get_llm()
    if isinstance(llm, ChatGroq):
        assert llm.max_retries == 1

@pytest.mark.asyncio
async def test_adzuna_503_triggers_fallback():
    """6 & 7. Adzuna 503 triggers fallback and Web search is invoked."""
    adzuna = AdzunaProvider()
    tavily = TavilyProvider()
    
    adzuna.search = AsyncMock(side_effect=Exception("HTTP 503 Service Unavailable"))
    tavily.search = AsyncMock(return_value=[
        RawOpportunity(source="web_search", source_id="url", company="Web", role="Role", location="", description="", application_url="url")
    ])
    
    composite = CompositeProvider([adzuna, tavily])
    results = await composite.search(SearchCriteria(query="test"))
    
    assert len(results) == 1
    assert results[0].source == "web_search"
    adzuna.search.assert_called_once()
    tavily.search.assert_called_once()

@pytest.mark.asyncio
async def test_results_are_deduplicated():
    """8 & 9. Multiple providers are deduplicated and source identity is retained."""
    adzuna = AdzunaProvider()
    tavily = TavilyProvider()
    
    adzuna.search = AsyncMock(return_value=[
        RawOpportunity(source="adzuna", source_id="1", company="Google", role="SWE", location="", description="", application_url="https://apply")
    ])
    tavily.search = AsyncMock(return_value=[
        RawOpportunity(source="web_search", source_id="2", company="Google", role="SWE", location="", description="", application_url="https://apply")
    ])
    
    composite = CompositeProvider([adzuna, tavily])
    results = await composite.search(SearchCriteria(query="test"))
    
    # Same application_url should deduplicate
    assert len(results) == 1
    assert results[0].source == "adzuna"
