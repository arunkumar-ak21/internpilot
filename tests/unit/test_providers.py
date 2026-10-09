"""Unit tests for the Opportunity Provider Abstraction (Phase 5)."""

import pytest
from unittest.mock import patch, MagicMock

from backend.providers.base import SearchCriteria, RawOpportunity
from backend.providers.mock import MockOpportunityProvider
from backend.providers.adzuna import AdzunaProvider
from backend.providers.factory import get_provider


@pytest.mark.asyncio
async def test_mock_provider():
    """Verify the mock provider returns valid formatted mock data."""
    provider = MockOpportunityProvider()
    criteria = SearchCriteria(query="Data Science", location="Remote", max_results=2)
    
    results = await provider.search(criteria)
    
    assert len(results) == 1  # Mock currently hardcodes 1 result for simplicity
    assert isinstance(results[0], RawOpportunity)
    assert results[0].source == "mock"
    assert "Data Science" in results[0].role
    assert results[0].location == "Remote"


def test_provider_factory_mock(monkeypatch):
    """Verify factory returns mock provider by default."""
    monkeypatch.setenv("OPPORTUNITY_PROVIDER", "mock")
    # clear cache to reload settings if needed or just patch the setting
    provider = get_provider("mock")
    assert isinstance(provider, MockOpportunityProvider)


def test_provider_factory_adzuna(monkeypatch):
    """Verify factory returns Adzuna provider when requested."""
    provider = get_provider("adzuna")
    assert isinstance(provider, AdzunaProvider)


@pytest.mark.asyncio
async def test_adzuna_provider_unconfigured():
    """Verify Adzuna provider raises error if called without credentials."""
    provider = AdzunaProvider(app_id="", app_key="")
    criteria = SearchCriteria(query="AI", location=None)
    
    with pytest.raises(ValueError, match="Adzuna provider is not configured"):
        await provider.search(criteria)


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_adzuna_provider_success(mock_get):
    """Verify Adzuna provider parses API results correctly."""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "results": [
            {
                "id": "12345",
                "title": "Machine Learning Intern",
                "company": {"display_name": "Tech Corp"},
                "location": {"display_name": "Bangalore"},
                "description": "A great internship.",
                "redirect_url": "https://example.com/apply"
            }
        ]
    }
    mock_get.return_value = mock_response

    provider = AdzunaProvider(app_id="fake_id", app_key="fake_key")
    criteria = SearchCriteria(query="Machine Learning", location="Bangalore")
    
    results = await provider.search(criteria)
    
    assert len(results) == 1
    assert isinstance(results[0], RawOpportunity)
    assert results[0].source == "adzuna"
    assert results[0].source_id == "12345"
    assert results[0].company == "Tech Corp"
    assert results[0].role == "Machine Learning Intern"
    assert results[0].location == "Bangalore"
    assert results[0].application_url == "https://example.com/apply"

    # Verify httpx was called correctly
    mock_get.assert_called_once()
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["app_id"] == "fake_id"
    assert kwargs["params"]["what"] == "Machine Learning"
    assert kwargs["params"]["where"] == "Bangalore"
