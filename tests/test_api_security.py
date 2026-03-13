from fastapi.testclient import TestClient
from catalyst.presentation.api.main import app, CATALYST_API_KEY

client = TestClient(app)


def test_health_check_is_public() -> None:
    """Verify that the health check endpoint remains public."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Catalyst is primed and ready.",
    }


def test_execute_without_api_key_fails() -> None:
    """Verify that accessing /execute without an API key returns 403."""
    response = client.post("/execute")
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid or missing API Key"}


def test_execute_with_invalid_api_key_fails() -> None:
    """Verify that accessing /execute with an invalid API key returns 403."""
    response = client.post("/execute", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid or missing API Key"}


def test_execute_with_valid_api_key_succeeds() -> None:
    """Verify that accessing /execute with a valid API key succeeds."""
    response = client.post("/execute", headers={"X-API-Key": CATALYST_API_KEY})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "results" in response.json()
    assert response.json()["results"]["load"] == "Data Loaded"
