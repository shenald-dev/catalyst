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
