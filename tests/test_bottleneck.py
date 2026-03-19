import asyncio
import time
import pytest
from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_generation_bottleneck() -> None:
    engine = WorkflowEngine()

    # Task A takes 0.5s
    async def task_a() -> str:
        await asyncio.sleep(0.5)
        return "A"

    # Task B takes 0.1s
    async def task_b() -> str:
        await asyncio.sleep(0.1)
        return "B"

    # Task C depends on B and takes 0.1s
    async def task_c() -> str:
        await asyncio.sleep(0.1)
        return "C"

    engine.add_task("A", task_a)
    engine.add_task("B", task_b)
    engine.add_task("C", task_c, ["B"])

    start = time.perf_counter()
    await engine.execute()
    end = time.perf_counter()

    # If it is level-synchronous, Generation 1 = [A, B].
    # Generation 2 = [C].
    # Generation 1 takes max(0.5, 0.1) = 0.5s
    # Generation 2 takes 0.1s
    # Total time = 0.6s
    #
    # If it is truly parallel async DAG, B finishes at 0.1s, C starts and finishes at 0.2s.
    # A finishes at 0.5s.
    # Total time = 0.5s

    duration = end - start
    print(f"Duration: {duration}")
    assert duration < 0.55  # True parallel DAG should take ~0.5s, not ~0.6s.
