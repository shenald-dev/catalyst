from fastapi.testclient import TestClient

from catalyst.presentation.api.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Catalyst is primed and ready.",
    }


def test_execute_workflow() -> None:
    response = client.post("/execute")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    results = data["results"]
    assert results["ingest"] == "Data Ingested"
    assert results["transform"] == "Data Transformed"
    assert results["load"] == "Data Loaded"
    assert results["fail"] == {"error": "Simulated failure", "task_name": "fail"}
    assert results["skipped"]["task_name"] == "skipped"
    assert "Skipped: upstream task 'fail' failed" in results["skipped"]["error"]
