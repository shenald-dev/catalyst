import asyncio
import time
import pytest
from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_sequential_vs_parallel() -> None:
    engine = WorkflowEngine()

    async def sleep_task_1() -> str:
        await asyncio.sleep(0.1)
        return "1"

    async def sleep_task_2() -> str:
        await asyncio.sleep(0.1)
        return "2"

    async def sleep_task_3() -> str:
        await asyncio.sleep(0.1)
        return "3"

    engine.add_task("task1", sleep_task_1)
    engine.add_task("task2", sleep_task_2)
    engine.add_task("task3", sleep_task_3)

    start_time = time.perf_counter()
    results = await engine.execute()
    end_time = time.perf_counter()

    duration = end_time - start_time
    # Since tasks run in parallel, 3 tasks taking 0.1s each should take roughly 0.1s total,
    # certainly less than 0.3s.
    assert duration < 0.2
    assert results == {"task1": "1", "task2": "2", "task3": "3"}


@pytest.mark.asyncio
async def test_dependencies_respected() -> None:
    engine = WorkflowEngine()
    execution_order: list[str] = []

    async def task_a() -> str:
        await asyncio.sleep(0.05)
        execution_order.append("A")
        return "A"

    async def task_b() -> str:
        execution_order.append("B")
        return "B"

    async def task_c() -> str:
        execution_order.append("C")
        return "C"

    engine.add_task("A", task_a)
    engine.add_task("B", task_b, ["A"])
    engine.add_task("C", task_c, ["A"])

    results = await engine.execute()

    assert execution_order[0] == "A"
    assert "B" in execution_order[1:]
    assert "C" in execution_order[1:]
    assert results == {"A": "A", "B": "B", "C": "C"}


def test_sync_tasks() -> None:
    engine = WorkflowEngine()

    def sync_task_1() -> str:
        return "sync_1"

    def sync_task_2() -> str:
        return "sync_2"

    engine.add_task("t1", sync_task_1)
    engine.add_task("t2", sync_task_2, ["t1"])

    results = asyncio.run(engine.execute())
    assert results == {"t1": "sync_1", "t2": "sync_2"}


@pytest.mark.asyncio
async def test_sync_task_does_not_block_async_task() -> None:
    engine = WorkflowEngine()

    sync_started = 0.0
    async_ended = 0.0

    def blocking_sync_task() -> str:
        nonlocal sync_started
        sync_started = time.perf_counter()
        time.sleep(0.5)
        return "sync"

    async def async_task() -> str:
        nonlocal async_ended
        # Give the event loop a chance to start the sync task if it's first
        await asyncio.sleep(0.1)
        async_ended = time.perf_counter()
        return "async"

    # Running these in parallel. If `blocking_sync_task` blocks the event loop,
    # `async_task` cannot resume until the 0.5s sleep is over.
    engine.add_task("sync", blocking_sync_task)
    engine.add_task("async", async_task)

    results = await engine.execute()

    # Check that async task finished roughly at 0.1s, far before the 0.5s sync task ends
    time_diff = async_ended - sync_started

    assert time_diff < 0.4, (
        f"Async task was blocked by sync task (time diff: {time_diff:.2f}s)"
    )
    assert results == {"sync": "sync", "async": "async"}
