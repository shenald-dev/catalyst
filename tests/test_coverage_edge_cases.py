import asyncio
import pytest
from catalyst.domain.engine import WorkflowEngine, TaskError


@pytest.mark.asyncio
async def test_run_node_missing_task() -> None:
    engine = WorkflowEngine()
    engine.add_task("A", lambda: "A")
    engine.tasks.pop("A")
    results = await engine.execute()
    assert isinstance(results["A"], TaskError)
    assert isinstance(results["A"].exception, KeyError)


@pytest.mark.asyncio
async def test_execute_base_exception_cancellation_coverage() -> None:
    engine = WorkflowEngine()

    async def task_a() -> str:
        raise asyncio.CancelledError()

    async def task_b() -> str:
        await asyncio.sleep(1)
        return "b"

    engine.add_task("a", task_a)
    engine.add_task("b", task_b)

    with pytest.raises(asyncio.CancelledError):
        await engine.execute()
