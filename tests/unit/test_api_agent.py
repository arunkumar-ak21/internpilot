"""Unit tests for the agent API endpoint (Lab 1 & 4)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from backend.main import app
from backend.skills.memory_manager import PreferenceExtraction


client = TestClient(app)


@pytest.fixture
def mock_db():
    # We patch the database repositories so we don't need a real SQLite DB during API tests
    with patch("backend.api.agent.SessionRepository") as mock_session, \
         patch("backend.api.agent.PreferenceRepository") as mock_pref:
        
        # Setup mocks
        session_instance = MagicMock()
        session_instance.get = AsyncMock(return_value=None)
        session_instance.save = AsyncMock()
        session_instance.audit = AsyncMock()
        mock_session.return_value = session_instance
        
        pref_instance = MagicMock()
        pref_instance.get_by_student_id = AsyncMock(return_value=None)
        pref_instance.save = AsyncMock()
        mock_pref.return_value = pref_instance
        
        yield session_instance, pref_instance


@patch("backend.api.agent.MemoryManager")
def test_agent_message_with_memory(mock_memory_manager, mock_db):
    """Test that sending a message extracts preferences and coordinates."""
    
    session_repo, pref_repo = mock_db
    
    # Mock Memory Manager
    memory_instance = MagicMock()
    mock_extraction = PreferenceExtraction(target_roles=["Data Scientist"], locations=["Remote"])
    memory_instance.extract_preferences = AsyncMock(return_value=mock_extraction)
    
    # Mock the merge to return a fake preference
    mock_merged = MagicMock()
    mock_merged.target_roles = ["Data Scientist"]
    mock_merged.locations = ["Remote"]
    mock_merged.minimum_stipend = None
    mock_merged.work_modes = None
    mock_merged.model_dump.return_value = {
        "target_roles": ["Data Scientist"],
        "locations": ["Remote"],
        "minimum_stipend": None,
        "work_modes": None
    }
    memory_instance.merge_preferences.return_value = mock_merged
    mock_memory_manager.return_value = memory_instance
    
    # Send a request
    response = client.post("/api/v1/agent/messages", json={
        "message": "I want a Data Scientist role in Remote",
        "student_id": "test-student"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["action"] == "search" # Because both role and location are satisfied by memory/message
    assert data["preferences"]["target_roles"] == ["Data Scientist"]
    assert data["preferences"]["locations"] == ["Remote"]
    
    # Verify the memory manager was called
    memory_instance.extract_preferences.assert_called_once()
    pref_repo.save.assert_called_once()
