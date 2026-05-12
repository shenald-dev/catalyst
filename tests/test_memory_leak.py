import asyncio
import gc
import weakref
from catalyst.domain.engine import WorkflowEngine


def test_no_memory_leak_in_run_node() -> None:
    """Ensure that executing a DAG does not leave a reference cycle that prevents task cleanup."""
    engine = WorkflowEngine()

    async def simple_task() -> str:
        return "ok"

    engine.add_task("task_a", simple_task)
    engine.add_task("task_b", simple_task, ["task_a"])

    task_refs = []

    async def run() -> None:
        tasks = {}
        engine._cached_topo_order = ["task_a", "task_b"]
        for node in engine._cached_topo_order:
            dep_tasks = tuple(tasks[d] for d in engine._predecessors.get(node, []))
            task = asyncio.create_task(engine._run_node(node, dep_tasks))
            tasks[node] = task
            task_refs.append(weakref.ref(task))

        await asyncio.gather(*tasks.values())
        # Clear references within the loop to allow garbage collection
        tasks.clear()

    # Run loop manually so we can close it and clean up tasks correctly
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run())
    finally:
        # Close loop to clear any internal references to tasks
        loop.close()
        asyncio.set_event_loop(None)

    # Force garbage collection multiple times
    gc.collect()

    # Check that all tasks are garbage collected
    for ref in task_refs:
        assert ref() is None, "Memory leak: task object was not garbage collected."
