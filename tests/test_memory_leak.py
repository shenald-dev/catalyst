import typing
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


@pytest.mark.asyncio
async def test_reference_cycle_is_broken() -> None:
    """Ensure that the execution dictionary is not held in a reference cycle."""
    engine = WorkflowEngine()

    async def my_task() -> str:
        return "success"

    engine.add_task("task_a", my_task)

    # Run the DAG once to let tasks evaluate and store references internally.
    results = await engine.execute()
    assert results["task_a"] == "success"

    weak_dep: typing.Any = None

    orig_run_node = engine._run_node

    # We create a dummy class to hold a reference to tasks so we can weakref it
    class TaskHolder:
        def __init__(self, tasks: tuple[asyncio.Task[typing.Any], ...]) -> None:
            self.tasks = tasks




    async def wrapped_run_node(node: str, dep_tasks: tuple[asyncio.Task[typing.Any], ...]) -> typing.Any:
        nonlocal weak_dep
        holder = TaskHolder(dep_tasks)
        weak_dep = weakref.ref(holder)
        return await orig_run_node(node, dep_tasks)

    engine._run_node = wrapped_run_node  # type: ignore

    await engine.execute()
    gc.collect()

    assert weak_dep() is None
