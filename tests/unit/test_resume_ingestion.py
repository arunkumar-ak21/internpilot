import pytest

from backend.services.resume_ingestion import parse_profile, resume_payload


def test_profile_parser_returns_only_explicit_email_and_skills():
    profile = parse_profile("Ada\nada@example.com\nPython, FastAPI")
    assert profile["email"] == "ada@example.com"
    assert profile["skills"] == ["fastapi", "python"]


def test_resume_rejects_mismatched_content_type_and_extension():
    with pytest.raises(ValueError):
        resume_payload("student-1", "resume.pdf", b"hello", "text/plain")
