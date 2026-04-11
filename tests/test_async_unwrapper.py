import asyncio
import functools
import pytest
from catalyst.domain.engine import WorkflowEngine


async def my_async_task(arg: str) -> str:
    await asyncio.sleep(0.1)
    return f"async {arg}"


@pytest.mark.asyncio
async def test_partial_async_task() -> None:
    engine = WorkflowEngine()

    # Create a partial wrapper around an async function
    partial_func = functools.partial(my_async_task, "partial")

    engine.add_task("test_partial", partial_func)

    # If the engine correctly detects it as async, it will await it on the event loop.
    # If it fails to detect it and treats it as sync, it will use asyncio.to_thread,
    # which works but incurs overhead and is incorrect.

    results = await engine.execute()

    assert results["test_partial"] == "async partial"

    # Check if the internal state recorded it as async correctly
    assert engine._is_async["test_partial"] is True, (
        "Failed to identify partial as async"
    )


@pytest.mark.asyncio
async def test_sync_callable_with_async_func_attribute_executes_safely() -> None:
    engine = WorkflowEngine()

    class SyncCallableAsyncFunc:
        async def func(self) -> str:
            return "async"

        def __call__(self) -> str:
            return "sync result"

    # Since it is a synchronous callable with merely a method named `func`,
    # it should be correctly evaluated as synchronous, avoiding TypeError during execute.
    engine.add_task("sync_with_async_attr", SyncCallableAsyncFunc())
    assert engine._is_async["sync_with_async_attr"] is False

    results = await engine.execute()
    assert results["sync_with_async_attr"] == "sync result"
