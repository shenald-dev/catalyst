import asyncio
import gc
import weakref
import pytest
from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_run_node_reference_cycle_prevention() -> None:
    """Ensure that the execution of a DAG does not create uncollectable reference cycles
    between the engine's tasks and the internal execution coroutines.
    """
    engine = WorkflowEngine()

    async def task_a() -> str:
        return "a"

    async def task_b() -> str:
        return "b"

    engine.add_task("A", task_a)
    engine.add_task("B", task_b, ["A"])

    # We track the engine itself to ensure it is collected.
    # If a cyclic reference exists internally, the engine or its internal structures
    # would stay alive longer than expected.
    engine_ref = weakref.ref(engine)

    await engine.execute()

    # Delete local references
    del engine

    # Force garbage collection
    gc.collect()

    # The engine should be fully collected, as no cyclic references should exist
    assert engine_ref() is None, "WorkflowEngine memory leak detected: circular reference preventing garbage collection."
