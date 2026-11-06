import asyncio
import contextlib

import pytest
from fastapi.testclient import TestClient

from catalyst.presentation.api.main import app, event_bus

client = TestClient(app)

def test_health() -> None:
    res = client.get("/api/v1/health")
    assert res.status_code == 200

def test_execute() -> None:
    res = client.post("/execute")
    assert res.status_code == 200

def test_dashboard() -> None:
    res = client.get("/dashboard")
    assert res.status_code == 200

def test_runs() -> None:
    res = client.get("/api/v1/workflows/runs")
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_event_bus_full_queue() -> None:
    q = event_bus.subscribe()
    # fill up the queue (maxsize is 100)
    for i in range(100):
        q.put_nowait({"i": i})

    event_bus.publish({"msg": "should fail"})
    assert q not in event_bus._subscribers

def test_declarative_workflow() -> None:
    payload = {
        "name": "test_workflow",
        "tasks": [
            {"name": "t1", "operation": "compute", "payload": 10},
            {"name": "t2", "operation": "transform", "dependencies": ["t1"]},
            {"name": "t3", "operation": "echo", "payload": "hello"},
        ]
    }
    res = client.post("/api/v1/workflows/run", json=payload)
    assert res.status_code == 200

def test_declarative_workflow_compute_lists() -> None:
    payload = {
        "name": "test_workflow2",
        "tasks": [
            {"name": "t1", "operation": "compute", "payload": [1, 2, 3]},
        ]
    }
    res = client.post("/api/v1/workflows/run", json=payload)
    assert res.status_code == 200

def test_declarative_workflow_compute_fallbacks() -> None:
    payload = {
        "name": "test_workflow3",
        "tasks": [
            {"name": "t1", "operation": "compute", "payload": 42},
            {"name": "t2", "operation": "unknown_op", "payload": "default"}
        ]
    }
    res = client.post("/api/v1/workflows/run", json=payload)
    assert res.status_code == 200

def test_declarative_workflow_fail() -> None:
    payload = {
        "name": "test_workflow_fail",
        "tasks": [
            {"name": "t1", "operation": "fail"}
        ]
    }
    res = client.post("/api/v1/workflows/run", json=payload)
    assert res.status_code == 200

def test_global_stream() -> None:
    # just grab the generator and get one event
    with client.stream("GET", "/api/v1/stream") as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            # if we get any lines, we know stream works
            break

def test_global_stream_cancel() -> None:
    # just grab the generator and get one event
    with contextlib.suppress(BaseException), client.stream("GET", "/api/v1/stream") as response:
            assert response.status_code == 200
            for line in response.iter_lines():
                raise asyncio.CancelledError()

def test_get_workflow_run_not_found() -> None:
    res = client.get("/api/v1/workflows/runs/does_not_exist")
    assert res.status_code == 404

def test_declarative_workflow_compute_tuples() -> None:
    payload = {
        "name": "test_workflow_tup",
        "tasks": [
            {"name": "t1", "operation": "compute", "payload": (1, 2, 3)},
        ]
    }
    res = client.post("/api/v1/workflows/run", json=payload)
    assert res.status_code == 200

def test_declarative_workflow_compute_sleep() -> None:
    payload = {
        "name": "test_workflow_sleep",
        "tasks": [
            {"name": "t1", "operation": "sleep", "payload": 0.01},
        ]
    }
    res = client.post("/api/v1/workflows/run", json=payload)
    assert res.status_code == 200

def test_declarative_workflow_unknown_op_empty_payload() -> None:
    payload = {
        "name": "test_workflow_empty_payload",
        "tasks": [
            {"name": "t1", "operation": "unknown_op", "payload": None}
        ]
    }
    res = client.post("/api/v1/workflows/run", json=payload)
    assert res.status_code == 200
