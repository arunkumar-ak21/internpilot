from backend.core.config import get_settings
from backend.core.database import sqlite_path


def test_settings_use_sqlite_by_default():
    assert get_settings().database_url.startswith("sqlite:///")


def test_sqlite_path_rejects_unsupported_database_url():
    try:
        sqlite_path("postgresql://localhost/internpilot")
    except ValueError as error:
        assert "Only sqlite" in str(error)
    else:
        raise AssertionError("Unsupported database URLs must be rejected")
