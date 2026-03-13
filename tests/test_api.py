from fastapi.testclient import TestClient
from catalyst.presentation.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test the health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Catalyst is primed and ready.",
    }


def test_execute_workflow() -> None:
    """Test the workflow execution endpoint."""
    response = client.post("/execute")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data
    results = data["results"]
    assert results["ingest"] == "Data Ingested"
    assert results["transform"] == "Data Transformed"
    assert results["load"] == "Data Loaded"
