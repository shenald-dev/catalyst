from fastapi.testclient import TestClient

from catalyst.presentation.api.main import app

client = TestClient(app)


def test_declarative_workflow_run() -> None:
    payload = {
        "name": "etl_pipeline",
        "tasks": [
            {"name": "extract", "operation": "echo", "payload": [10, 20, 30]},
            {"name": "sleep_step", "operation": "sleep", "payload": 0.01, "dependencies": ["extract"]},
            {"name": "aggregate", "operation": "compute", "dependencies": ["extract"]},
        ],
        "max_concurrency": 2,
    }

    response = client.post("/api/v1/workflows/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "run_id" in data
    assert data["results"]["extract"] == [10, 20, 30]
    assert "Slept 0.01s" in data["results"]["sleep_step"]
    assert data["results"]["aggregate"] == 60.0

    run_id = data["run_id"]

    # Verify run history inspection
    get_res = client.get(f"/api/v1/workflows/runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["run_id"] == run_id
    assert get_res.json()["name"] == "etl_pipeline"


def test_declarative_workflow_with_failure_and_retries() -> None:
    payload = {
        "name": "faulty_pipeline",
        "tasks": [
            {"name": "bad_task", "operation": "fail", "payload": "Database down", "retries": 1},
            {"name": "dependent_task", "operation": "echo", "payload": "ok", "dependencies": ["bad_task"]},
        ],
    }

    response = client.post("/api/v1/workflows/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "failure"
    assert data["results"]["bad_task"]["error"] == "Database down"
    assert "Skipped: upstream task 'bad_task' failed" in data["results"]["dependent_task"]["error"]
    assert data["task_metrics"]["bad_task"]["retries_count"] == 1


def test_list_workflow_runs() -> None:
    response = client.get("/api/v1/workflows/runs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert isinstance(data["runs"], list)


def test_system_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "version" in data
    assert "uptime_seconds" in data


def test_dashboard_ui_html() -> None:
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Catalyst Engine" in response.text
    assert "Interactive DAG Topology" in response.text


def test_stream_sse_endpoint() -> None:
    with client.stream("GET", "/api/v1/stream") as stream:
        lines = []
        for line in stream.iter_lines():
            if line:
                lines.append(line)
            if len(lines) >= 2:
                break
        assert any("event: connected" in l or "connected" in l for l in lines)


def test_run_not_found() -> None:
    response = client.get("/api/v1/workflows/runs/non_existent_id")
    assert response.status_code == 404
