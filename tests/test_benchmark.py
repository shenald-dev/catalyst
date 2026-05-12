import time
import pytest
from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_performance_benchmark() -> None:
    """Benchmark DAG execution to ensure hot-path optimizations are effective."""
    engine = WorkflowEngine()

    async def fast_task() -> str:
        return "ok"

    # Create a deep and wide DAG
    num_layers = 10
    tasks_per_layer = 100

    # Layer 0
    for i in range(tasks_per_layer):
        engine.add_task(f"task_0_{i}", fast_task)

    # Subsequent layers
    for layer in range(1, num_layers):
        prev_layer_deps = [f"task_{layer - 1}_{i}" for i in range(tasks_per_layer)]
        for i in range(tasks_per_layer):
            engine.add_task(f"task_{layer}_{i}", fast_task, prev_layer_deps)

    start_time = time.perf_counter()
    results = await engine.execute()
    end_time = time.perf_counter()

    duration = end_time - start_time
    assert len(results) == num_layers * tasks_per_layer
    # Ensure it runs reasonably fast (e.g., under 1 second for 1000 tasks with many edges)
    assert duration < 2.0, f"Execution took too long: {duration:.2f} seconds"
