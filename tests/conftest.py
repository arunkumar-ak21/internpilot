"""Shared test configuration for InternPilot."""

from __future__ import annotations

import pytest

import asyncio
from backend.core.config import get_settings
from backend.core.database import initialize_database


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Prevent tests from creating or reading the developer database."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'internpilot-test.db'}")
    get_settings.cache_clear()
    asyncio.run(initialize_database())
    yield
    get_settings.cache_clear()
