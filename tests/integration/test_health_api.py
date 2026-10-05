from fastapi.testclient import TestClient

from backend.main import create_app


def test_health_endpoint_reports_running_service():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint_reports_initialized_database():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["database"] == "ready"
