"""Shared test configuration for InternPilot."""

from __future__ import annotations

import pytest

from backend.core.config import get_settings


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Prevent tests from creating or reading the developer database."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'internpilot-test.db'}")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
