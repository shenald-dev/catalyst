from fastapi.testclient import TestClient

from catalyst.presentation.api.main import app

client = TestClient(app)

def test_global_stream_loop() -> None:
    # just grab the generator and get one event
    with client.stream("GET", "/api/v1/stream") as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            # if we get any lines, we know stream works
            break
