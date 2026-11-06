import asyncio

import pytest

from catalyst.domain.engine import TaskError, WorkflowEngine


class AsyncCallable:
    async def __call__(self) -> str:
        return "async_result"

@pytest.mark.asyncio
async def test_callable_class_is_async() -> None:
    engine = WorkflowEngine()
    engine.add_task("A", AsyncCallable())
    assert engine._is_async["A"] is True
    res = await engine.execute()
    assert res["A"] == "async_result"

@pytest.mark.asyncio
async def test_listener_coro() -> None:
    engine = WorkflowEngine()

    async def my_listener(event: object) -> None:
        pass

    engine.add_listener(my_listener)
    engine.add_task("A", lambda: "A")
    await engine.execute()
    assert len(engine._listeners) == 1

@pytest.mark.asyncio
async def test_listener_exception() -> None:
    engine = WorkflowEngine()

    def my_listener(event: object) -> None:
        raise ValueError("error")

    engine.add_listener(my_listener)
    engine.add_task("A", lambda: "A")
    res = await engine.execute()
    assert res

@pytest.mark.asyncio
async def test_run_node_single_dep_cancelled() -> None:
    engine = WorkflowEngine()

    async def my_dep() -> None:
        await asyncio.sleep(0.5)

    engine.add_task("dep", my_dep)
    engine.add_task("node", lambda: "ok", ["dep"])

    # Run _run_node manually and cancel it to hit the except asyncio.CancelledError on shield
    task_dep = asyncio.create_task(engine._run_node("dep", ()))
    task_node = asyncio.create_task(engine._run_node("node", (task_dep,)))

    await asyncio.sleep(0.1)
    task_node.cancel()

    try:
        await task_node
    except asyncio.CancelledError:
        pass

    await task_dep # should not be cancelled!

@pytest.mark.asyncio
async def test_run_node_single_dep_cancelled_from_source() -> None:
    engine = WorkflowEngine()

    async def my_dep() -> None:
        raise asyncio.CancelledError()

    engine.add_task("dep", my_dep)
    engine.add_task("node", lambda: "ok", ["dep"])

    # Run _run_node manually
    task_dep = asyncio.create_task(engine._run_node("dep", ()))
    task_node = asyncio.create_task(engine._run_node("node", (task_dep,)))

    res = await task_node
    assert isinstance(res, TaskError)

@pytest.mark.asyncio
async def test_run_node_multiple_dep_exception_base_exception() -> None:
    engine = WorkflowEngine()

    async def my_dep1() -> None:
        raise BaseException("System exit")  # noqa: TRY002

    async def my_dep2() -> None:
        await asyncio.sleep(0.5)

    engine.add_task("dep1", my_dep1)
    engine.add_task("dep2", my_dep2)
    engine.add_task("node", lambda: "ok", ["dep1", "dep2"])

    # Run _run_node manually
    task_dep1 = asyncio.create_task(engine._run_node("dep1", ()))
    task_dep2 = asyncio.create_task(engine._run_node("dep2", ()))

    # Actually _run_node handles exception from task, but the callback inside it _on_dep_done can catch BaseException
    task_node = asyncio.create_task(engine._run_node("node", (task_dep1, task_dep2)))

    with pytest.raises(BaseException):  # noqa: B017
        await task_node

@pytest.mark.asyncio
async def test_run_node_multiple_dep_exception_cancelled_again() -> None:
    engine = WorkflowEngine()

    async def my_dep1() -> None:
        raise asyncio.CancelledError()

    async def my_dep2() -> None:
        await asyncio.sleep(0.5)

    engine.add_task("dep1", my_dep1)
    engine.add_task("dep2", my_dep2)
    engine.add_task("node", lambda: "ok", ["dep1", "dep2"])

    # Run _run_node manually
    task_dep1 = asyncio.create_task(engine._run_node("dep1", ()))
    task_dep2 = asyncio.create_task(engine._run_node("dep2", ()))

    # Actually _run_node handles exception from task, but the callback inside it _on_dep_done can catch asyncio.CancelledError
    task_node = asyncio.create_task(engine._run_node("node", (task_dep1, task_dep2)))

    res = await task_node
    assert isinstance(res, TaskError)
