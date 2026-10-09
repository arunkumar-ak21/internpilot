import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_resume_upload_starts_workflow():
    response = client.post(
        "/api/v1/resumes/upload",
        data={"student_id": "test-123"},
        files={"file": ("resume.txt", b"Skills: Python, SQL, React. Education: BS CS.", "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "workflow_id" in data
    assert data["profile_status"] in ["completed", "partial", "failed"]
    
    workflow_id = data["workflow_id"]
    status_response = client.get(f"/api/v1/workflows/{workflow_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    # It might have advanced to 'discovering' since background task started
    assert status_data["status"] in ["profile_ready", "discovering", "completed", "failed", "partial_success", "search_failed", "no_results"]

def test_chat_without_workflow():
    response = client.post(
        "/api/v1/agent/messages",
        json={"message": "List my skills", "student_id": "test-123", "session_id": "test-sess-1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
