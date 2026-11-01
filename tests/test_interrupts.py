import asyncio
import sys

import pytest

from catalyst.domain.engine import TaskError, WorkflowEngine


@pytest.mark.asyncio
async def test_cancelled_error_becomes_task_error() -> None:
    engine = WorkflowEngine()

    async def raise_cancel() -> str:
        # Simulate a task failing due to a cancellation exception
        raise asyncio.CancelledError()

    engine.add_task("cancel", raise_cancel)

    results = await engine.execute()
    assert isinstance(results["cancel"], TaskError)
    assert isinstance(results["cancel"].exception, asyncio.CancelledError)


@pytest.mark.asyncio
async def test_engine_execute_cancellation() -> None:
    engine = WorkflowEngine()

    async def long_task() -> str:
        await asyncio.sleep(10)
        return "done"

    engine.add_task("long", long_task)

    task = asyncio.create_task(engine.execute())

    # Let it start
    await asyncio.sleep(0.01)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task


def test_keyboard_interrupt_propagates_sync() -> None:
    engine = WorkflowEngine()

    def raise_interrupt() -> str:
        raise KeyboardInterrupt("ctrl-c")

    engine.add_task("interrupt", raise_interrupt)

    with pytest.raises(KeyboardInterrupt):
        asyncio.run(engine.execute())


def test_system_exit_propagates_sync() -> None:
    engine = WorkflowEngine()

    def raise_exit() -> str:
        sys.exit(1)

    engine.add_task("exit", raise_exit)

    with pytest.raises(SystemExit):
        asyncio.run(engine.execute())
