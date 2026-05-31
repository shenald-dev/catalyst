import pytest
import asyncio
import gc
import weakref
from catalyst.domain.engine import WorkflowEngine

@pytest.mark.asyncio
async def test_no_task_leak():
    engine = WorkflowEngine()

    async def fast_task():
        return "done"

    engine.add_task("task_1", fast_task)
    engine.add_task("task_2", fast_task, dependencies=["task_1"])
    engine.add_task("task_3", fast_task, dependencies=["task_2"])

    await engine.execute()

    # Check if the tasks dict does not contain strong circular references to asyncio.Task
    # Wait to ensure execution has fully cleared
    await asyncio.sleep(0.01)

    # We can check that memory is cleared
    engine_ref = weakref.ref(engine)
    del engine

    # Force a garbage collection cycle
    gc.collect()

    # If there's no reference cycle, the engine should be garbage collected
    # We may need to be careful as the loop might still hold some references, but our fix broke the primary cycle
    assert engine_ref() is None
