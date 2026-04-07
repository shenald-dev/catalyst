import asyncio
import time
import pytest
from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_true_fail_fast_multiple_deps() -> None:
    engine = WorkflowEngine()

    downstream_eval_time = None

    async def slow_success() -> str:
        await asyncio.sleep(0.5)
        return "slow"

    async def fast_fail() -> str:
        await asyncio.sleep(0.1)
        raise ValueError("failed early")

    async def downstream() -> str:
        return "should skip"

    engine.add_task("slow", slow_success)
    engine.add_task("fail", fast_fail)

    engine.add_task("downstream", downstream, ["slow", "fail"])

    # Wrap the _run_node slightly just for testing
    orig_run_node = engine._run_node

    from typing import Any, Dict

    async def wrapped_run_node(
        node: str, results: Dict[str, Any], tasks: Dict[str, asyncio.Task[Any]]
    ) -> Any:
        nonlocal downstream_eval_time
        res = await orig_run_node(node, results, tasks)
        if node == "downstream":
            downstream_eval_time = time.perf_counter()
        return res

    engine._run_node = wrapped_run_node  # type: ignore

    start = time.perf_counter()
    await engine.execute()

    # downstream_eval_time should be around start + 0.1s
    assert downstream_eval_time is not None
    eval_duration = downstream_eval_time - start

    assert eval_duration < 0.2, (
        "Downstream did not fail fast, waited for slow dependency!"
    )
