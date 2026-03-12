import pytest
from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_execute_raises_value_error_on_cycle() -> None:
    engine = WorkflowEngine()

    async def task_a() -> str:
        return "A"

    async def task_b() -> str:
        return "B"

    # Create a cycle: A depends on B, B depends on A
    engine.add_task("task_a", task_a, dependencies=["task_b"])
    engine.add_task("task_b", task_b, dependencies=["task_a"])

    with pytest.raises(
        ValueError, match="Workflow must be a Directed Acyclic Graph \\(DAG\\)"
    ):
        await engine.execute()
