import asyncio
import pytest
from catalyst.domain.engine import WorkflowEngine


def test_add_task() -> None:
    engine = WorkflowEngine()

    def sync_task() -> int:
        return 1

    engine.add_task("task1", sync_task)
    assert "task1" in engine.graph.nodes
    assert engine.tasks["task1"] == sync_task

    def sync_task2() -> int:
        return 2

    engine.add_task("task2", sync_task2, dependencies=["task1"])
    assert "task2" in engine.graph.nodes
    assert engine.tasks["task2"] == sync_task2
    assert ("task1", "task2") in engine.graph.edges


@pytest.mark.asyncio
async def test_execute_success() -> None:
    engine = WorkflowEngine()

    def sync_task1() -> int:
        return 10

    async def async_task2() -> int:
        await asyncio.sleep(0.01)
        return 20

    def sync_task3() -> int:
        return 30

    engine.add_task("task1", sync_task1)
    engine.add_task("task2", async_task2, dependencies=["task1"])
    engine.add_task("task3", sync_task3, dependencies=["task1", "task2"])

    results = await engine.execute()
    assert results == {"task1": 10, "task2": 20, "task3": 30}


@pytest.mark.asyncio
async def test_execute_cyclic_graph() -> None:
    engine = WorkflowEngine()

    def task1() -> None:
        pass

    def task2() -> None:
        pass

    engine.add_task("task1", task1, dependencies=["task2"])
    engine.add_task("task2", task2, dependencies=["task1"])

    with pytest.raises(
        ValueError, match=r"Workflow must be a Directed Acyclic Graph \(DAG\)"
    ):
        await engine.execute()
