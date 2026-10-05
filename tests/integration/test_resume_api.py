from fastapi.testclient import TestClient

from backend.main import create_app


def test_resume_upload_preserves_metadata_and_returns_derived_profile():
    with TestClient(create_app()) as client:
        response = client.post("/api/v1/resumes/upload", data={"student_id": "student-1"}, files={"file": ("resume.txt", b"Student\nstudent@example.com\nPython SQL", "text/plain")})
    assert response.status_code == 200
    assert response.json()["parsed_profile"]["skills"] == ["python", "sql"]
