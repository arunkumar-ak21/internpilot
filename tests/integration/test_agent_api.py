from fastapi.testclient import TestClient

from backend.main import create_app


def test_agent_persists_session_and_revises_plan_after_clarification():
    with TestClient(create_app()) as client:
        first = client.post("/api/v1/agent/messages", json={"message": "I want an AI internship"}).json()
        second = client.post("/api/v1/agent/messages", json={"session_id": first["session_id"], "message": "in Bangalore"})
    assert first["action"] == "clarify"
    assert second.json()["action"] == "search"
