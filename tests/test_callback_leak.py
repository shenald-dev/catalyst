import asyncio

import typing
import pytest

from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_dependency_callback_leak() -> None:
    """Ensure that fail-fast does not leak callbacks on slow upstream tasks."""
    engine = WorkflowEngine()

    async def slow_task() -> str:
        await asyncio.sleep(0.5)
        return "slow"

    async def fast_fail() -> str:
        raise ValueError("fail")

    async def downstream() -> str:
        return "down"

    engine.add_task("slow", slow_task)
    engine.add_task("fail", fast_fail)
    engine.add_task("down", downstream, ["slow", "fail"])

    original_run_node = engine._run_node

    cb_names = []

    async def my_run_node(
        node: str, dep_tasks: tuple[asyncio.Task[typing.Any], ...]
    ) -> typing.Any:
        res = await original_run_node(node, dep_tasks)
        if node == "down":
            for t in dep_tasks:
                if not t.done():
                    callbacks = getattr(t, "_callbacks", [])
                    if callbacks is None:
                        callbacks = []
                    for cb in callbacks:
                        if isinstance(cb, tuple):
                            func = cb[0]
                            cb_names.append(func.__name__)
                        else:
                            cb_names.append(getattr(cb, "__name__", str(cb)))
        return res

    engine._run_node = my_run_node  # type: ignore

    await engine.execute()

    assert "_on_dep_done" not in cb_names, (
        f"Leaked callback found! Callbacks: {cb_names}"
    )
