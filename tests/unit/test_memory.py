"""Unit tests for the Memory & Retrieval Skill (Phase 7)."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from backend.skills.memory_manager import MemoryManager, PreferenceExtraction
from backend.models.schemas import CandidatePreference, WorkMode


@pytest.mark.asyncio
async def test_memory_extraction():
    """Test the memory manager extracts preferences from text."""
    
    manager = MemoryManager()
    
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=PreferenceExtraction(
        target_roles=["Backend Engineer"],
        locations=["London"],
        work_modes=["remote"],
        minimum_stipend=1000
    ))
    manager.chain = mock_chain
    
    extraction = await manager.extract_preferences("I want a remote backend engineering internship in London for at least £1000.")
    
    assert extraction.target_roles == ["Backend Engineer"]
    assert extraction.locations == ["London"]
    assert extraction.work_modes == ["remote"]
    assert extraction.minimum_stipend == 1000
    
    mock_chain.ainvoke.assert_called_once()


def test_memory_merge_new():
    """Test merging extraction into a blank preference."""
    manager = MemoryManager()
    
    existing = CandidatePreference(student_id="test-student")
    extraction = PreferenceExtraction(
        target_roles=["Frontend"],
        locations=["Paris"],
        work_modes=["remote"],
        minimum_stipend=500
    )
    
    updated = manager.merge_preferences(existing, extraction)
    
    assert "Frontend" in updated.target_roles
    assert "Paris" in updated.locations
    assert WorkMode.REMOTE in updated.work_modes
    assert updated.minimum_stipend == 500


def test_memory_merge_append():
    """Test merging extraction appends to existing preferences."""
    manager = MemoryManager()
    
    existing = CandidatePreference(
        student_id="test-student",
        target_roles=["Backend"],
        locations=["London"],
        work_modes=[WorkMode.HYBRID],
        minimum_stipend=1000
    )
    
    extraction = PreferenceExtraction(
        target_roles=["Frontend"],
        locations=["Paris"],
        work_modes=["remote"],
        minimum_stipend=500 # Should not override because it's lower
    )
    
    updated = manager.merge_preferences(existing, extraction)
    
    assert "Backend" in updated.target_roles
    assert "Frontend" in updated.target_roles
    assert "London" in updated.locations
    assert "Paris" in updated.locations
    assert WorkMode.HYBRID in updated.work_modes
    assert WorkMode.REMOTE in updated.work_modes
    
    # Minimum stipend should remain the higher value
    assert updated.minimum_stipend == 1000
