from fastapi.testclient import TestClient

from backend.main import create_app


def test_tool_endpoints_validate_and_return_labelled_mock_data():
    with TestClient(create_app()) as client:
        calculation = client.post("/api/v1/tools/calculator", json={"expression": "2 + 3 * 4"})
        search = client.post("/api/v1/tools/search", json={"query": "AI/ML", "location": "Bangalore"})
    assert calculation.json() == {"result": 14.0}
    assert search.json()["source"] == "mock"
    assert search.json()["opportunities"][0]["source"] == "mock"
