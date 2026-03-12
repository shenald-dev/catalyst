from fastapi.testclient import TestClient

from catalyst.presentation.api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Catalyst is primed and ready.",
    }


def test_execute_workflow():
    response = client.post("/execute")
    assert response.status_code == 200
    expected_response = {
        "status": "success",
        "results": {
            "ingest": "Data Ingested",
            "transform": "Data Transformed",
            "load": "Data Loaded",
        },
    }
    assert response.json() == expected_response
