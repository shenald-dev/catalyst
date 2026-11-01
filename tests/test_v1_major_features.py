import asyncio
from typing import Any

import pytest

from catalyst import (
    RetryPolicy,
    TaskError,
    WorkflowEngine,
    WorkflowEvent,
    WorkflowResult,
)


@pytest.mark.asyncio
async def test_data_passing_single_positional() -> None:
    """A downstream task with 1 dependency can receive the upstream result as a single argument."""
    engine = WorkflowEngine()

    async def fetch_users() -> list[str]:
        return ["Alice", "Bob"]

    async def process_users(users: list[str]) -> str:
        return f"Processed: {', '.join(users)}"

    engine.add_task("fetch", fetch_users)
    engine.add_task("process", process_users, dependencies=["fetch"])

    results = await engine.execute()
    assert results["fetch"] == ["Alice", "Bob"]
    assert results["process"] == "Processed: Alice, Bob"


@pytest.mark.asyncio
async def test_data_passing_named_keywords() -> None:
    """A downstream task can declare parameter names matching upstream task names."""
    engine = WorkflowEngine()

    async def fetch_a() -> int:
        return 10

    async def fetch_b() -> int:
        return 25

    async def sum_values(fetch_a: int, fetch_b: int) -> int:
        return fetch_a + fetch_b

    engine.add_task("fetch_a", fetch_a)
    engine.add_task("fetch_b", fetch_b)
    engine.add_task("sum_values", sum_values, dependencies=["fetch_a", "fetch_b"])

    results = await engine.execute()
    assert results["sum_values"] == 35


@pytest.mark.asyncio
async def test_data_passing_var_positional() -> None:
    """A downstream task with *args receives upstream results in dependency order."""
    engine = WorkflowEngine()

    engine.add_task("val1", lambda: "A")
    engine.add_task("val2", lambda: "B")
    engine.add_task("val3", lambda: "C")

    def aggregate(*args: str) -> str:
        return "-".join(args)

    engine.add_task("agg", aggregate, dependencies=["val1", "val2", "val3"])

    results = await engine.execute()
    assert results["agg"] == "A-B-C"


@pytest.mark.asyncio
async def test_data_passing_context_dict() -> None:
    """A task with a 'context' parameter receives a dictionary of upstream results."""
    engine = WorkflowEngine()

    engine.add_task("source_1", lambda: 100)
    engine.add_task("source_2", lambda: 200)

    async def handler(context: dict[str, Any]) -> int:
        return int(context["source_1"]) + int(context["source_2"])

    engine.add_task("handler", handler, dependencies=["source_1", "source_2"])

    results = await engine.execute()
    assert results["handler"] == 300


@pytest.mark.asyncio
async def test_retry_policy_recovers_on_retry() -> None:
    """A flaky task succeeds after retrying when a RetryPolicy is applied."""
    engine = WorkflowEngine()
    attempts = 0

    async def flaky_task() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError(f"Transient error on attempt {attempts}")
        return "reconnected"

    engine.add_task(
        "flaky",
        flaky_task,
        retry_policy=RetryPolicy(max_retries=3, delay=0.01, backoff=1.5, jitter=False),
    )

    results = await engine.execute()
    assert results["flaky"] == "reconnected"
    assert attempts == 3
    assert results.task_metrics["flaky"].retries_count == 2
    assert results.task_metrics["flaky"].status == "success"


@pytest.mark.asyncio
async def test_retry_policy_exhausts_and_fails() -> None:
    """A task that persistently fails records a TaskError after retries are exhausted."""
    engine = WorkflowEngine()
    attempts = 0

    async def broken_task() -> str:
        nonlocal attempts
        attempts += 1
        raise ValueError("Fatal error")

    engine.add_task(
        "broken",
        broken_task,
        retry_policy=RetryPolicy(max_retries=2, delay=0.01, jitter=False),
    )

    results = await engine.execute()
    assert isinstance(results["broken"], TaskError)
    assert attempts == 3  # initial attempt + 2 retries
    assert results.status == "failure"
    assert results.task_metrics["broken"].retries_count == 2
    assert results.task_metrics["broken"].status == "failed"


@pytest.mark.asyncio
async def test_concurrency_limiter() -> None:
    """Enforces that simultaneous running tasks never exceed max_concurrency."""
    max_concurrency = 3
    engine = WorkflowEngine(max_concurrency=max_concurrency)

    current_concurrent = 0
    peak_concurrent = 0

    async def worker() -> None:
        nonlocal current_concurrent, peak_concurrent
        current_concurrent += 1
        peak_concurrent = max(peak_concurrent, current_concurrent)
        await asyncio.sleep(0.05)
        current_concurrent -= 1

    for i in range(12):
        engine.add_task(f"worker_{i}", worker)

    results = await engine.execute()
    assert len(results) == 12
    assert peak_concurrent <= max_concurrency


@pytest.mark.asyncio
async def test_workflow_events_and_listeners() -> None:
    """WorkflowEngine emits lifecycle events to registered listeners."""
    engine = WorkflowEngine()
    events: list[WorkflowEvent] = []

    engine.add_listener(lambda evt: events.append(evt))

    engine.add_task("task_a", lambda: "a")
    engine.add_task("task_b", lambda: "b", dependencies=["task_a"])

    results = await engine.execute()
    assert results["task_b"] == "b"

    event_types = [e.event_type for e in events]
    assert "workflow_started" in event_types
    assert "task_started" in event_types
    assert "task_completed" in event_types
    assert "workflow_completed" in event_types


@pytest.mark.asyncio
async def test_task_decorator_syntax() -> None:
    """Tasks can be registered intuitively using the @engine.task decorator."""
    engine = WorkflowEngine()

    @engine.task()
    async def step_1() -> str:
        return "hello"

    @engine.task(dependencies=["step_1"])
    async def step_2(step_1: str) -> str:
        return f"{step_1} world"

    assert callable(step_1) and callable(step_2)
    results = await engine.execute()
    assert results["step_2"] == "hello world"


@pytest.mark.asyncio
async def test_workflow_result_telemetry() -> None:
    """WorkflowResult provides dictionary compatibility and rich metrics serialization."""
    engine = WorkflowEngine()

    engine.add_task("step_fast", lambda: 1)
    results = await engine.execute()

    assert isinstance(results, dict)
    assert isinstance(results, WorkflowResult)
    assert results["step_fast"] == 1

    d = results.to_dict()
    assert d["status"] == "success"
    assert "total_duration_ms" in d
    assert "step_fast" in d["task_metrics"]
    assert d["task_metrics"]["step_fast"]["status"] == "success"
