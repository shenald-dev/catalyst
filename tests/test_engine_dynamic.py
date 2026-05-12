import pytest
from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_dynamic_dependency_resolution() -> None:
    """Ensure dependencies passed as tuples dynamically evaluate correctly."""
    engine = WorkflowEngine()

    async def fast_task() -> str:
        return "ok"

    engine.add_task("A", fast_task)
    engine.add_task("B", fast_task, ["A"])
    engine.add_task("C", fast_task, ["B"])

    results = await engine.execute()
    assert results["A"] == "ok"
    assert results["B"] == "ok"
    assert results["C"] == "ok"

    # Now mutate the predecessors dictionary dynamically
    engine.add_task("D", fast_task)
    engine.add_task("A", fast_task, ["D"])

    # Engine cache should be reset
    assert engine._cached_topo_order is None

    results = await engine.execute()
    assert results["D"] == "ok"
    assert results["A"] == "ok"
    assert results["B"] == "ok"
    assert results["C"] == "ok"
