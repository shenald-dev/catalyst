import asyncio
import gc
import weakref
import pytest
from catalyst.domain.engine import WorkflowEngine, TaskError

@pytest.mark.asyncio
async def test_reference_cycle_is_broken() -> None:
    """Ensure that the execution dictionary is not held in a reference cycle."""
    engine = WorkflowEngine()

    async def my_task():
        return "success"

    engine.add_task("task_a", my_task)

    # Run the DAG once to let tasks evaluate and store references internally.
    results = await engine.execute()
    assert results["task_a"] == "success"

    weak_dep = None

    orig_run_node = engine._run_node

    # We create a dummy class to hold a reference to tasks so we can weakref it
    class TaskHolder:
        def __init__(self, tasks):
            self.tasks = tasks

    async def wrapped_run_node(node: str, dep_tasks: tuple[asyncio.Task, ...]):
        nonlocal weak_dep
        holder = TaskHolder(dep_tasks)
        weak_dep = weakref.ref(holder)
        return await orig_run_node(node, dep_tasks)

    engine._run_node = wrapped_run_node

    await engine.execute()
    gc.collect()

    assert weak_dep() is None