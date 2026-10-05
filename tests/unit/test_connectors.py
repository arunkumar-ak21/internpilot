"""Unit tests for the MCP-Style Connectors (Phase 8)."""

import pytest
import os
from pathlib import Path

from backend.connectors.file_connector import FileConnector
from backend.connectors.db_connector import DatabaseConnector
from backend.connectors.api_connector import APIConnector
from backend.connectors.base import Resource


@pytest.fixture
def temp_uploads_dir(tmp_path):
    """Fixture providing a temporary uploads directory."""
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    # Create a test file
    (uploads / "test.txt").write_text("hello world")
    return uploads


@pytest.mark.asyncio
async def test_file_connector_read(temp_uploads_dir):
    """Test reading a valid file."""
    connector = FileConnector(allowed_directory=temp_uploads_dir)
    content = await connector.read("test.txt")
    assert content == "hello world"


@pytest.mark.asyncio
async def test_file_connector_list(temp_uploads_dir):
    """Test listing files."""
    connector = FileConnector(allowed_directory=temp_uploads_dir)
    resources = await connector.list_resources()
    assert len(resources) == 1
    assert isinstance(resources[0], Resource)
    assert resources[0].id == "test.txt"


@pytest.mark.asyncio
async def test_file_connector_traversal_protection(temp_uploads_dir):
    """Test that path traversal attempts are blocked."""
    connector = FileConnector(allowed_directory=temp_uploads_dir)
    
    # Try to access a file outside the directory
    with pytest.raises(PermissionError, match="outside the allowed directory"):
        await connector.read("../secret.txt")


@pytest.mark.asyncio
async def test_db_connector_denies_writes():
    """Test that DB connector rejects writes."""
    connector = DatabaseConnector("sqlite:///:memory:")
    with pytest.raises(PermissionError):
        await connector.write("sessions", {"data": "test"})


@pytest.mark.asyncio
async def test_db_connector_denies_arbitrary_reads():
    """Test that DB connector rejects arbitrary table reads."""
    connector = DatabaseConnector("sqlite:///:memory:")
    with pytest.raises(ValueError, match="not an accessible table"):
        await connector.read("sqlite_master")


@pytest.mark.asyncio
async def test_api_connector_requires_query():
    """Test that API connector read requires a query param."""
    connector = APIConnector()
    with pytest.raises(ValueError, match="requires a 'query' parameter"):
        await connector.read("opportunity_search", params={})


@pytest.mark.asyncio
async def test_api_connector_denies_writes():
    """Test that API connector rejects writes."""
    connector = APIConnector()
    with pytest.raises(PermissionError):
        await connector.write("opportunity_search", {"data": "test"})
