import asyncio

import pytest

from catalyst.domain.engine import TaskError, WorkflowEngine


@pytest.mark.asyncio
async def test_multiple_dependency_upstream_cancel() -> None:
    engine = WorkflowEngine()

    async def task_a() -> str:
        raise asyncio.CancelledError()

    async def task_a2() -> str:
        return "a2"

    async def task_b() -> str:
        return "b"

    engine.add_task("a", task_a)
    engine.add_task("a2", task_a2)
    engine.add_task("b", task_b, ["a", "a2"])

    results = await engine.execute()

    assert isinstance(results["a"], TaskError)
    assert isinstance(results["a"].exception, asyncio.CancelledError)
    assert results["a2"] == "a2"
    assert isinstance(results["b"], TaskError)
    assert "upstream task 'a' failed" in str(results["b"].exception)
