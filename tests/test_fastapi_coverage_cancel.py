import asyncio

import pytest

from catalyst.presentation.api.main import event_bus, global_event_stream


@pytest.mark.asyncio
async def test_sse_generator_cancel() -> None:
    res = await global_event_stream()

    # Need to run it and cancel it
    gen = res.body_iterator

    async def run_gen() -> None:
        async for i in gen:
            break

    t = asyncio.create_task(run_gen())
    await asyncio.sleep(0.01)
    t.cancel()

    try:
        await t
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_sse_generator_message() -> None:
    res = await global_event_stream()

    # Need to run it and cancel it
    gen = res.body_iterator

    async def run_gen() -> None:
        count = 0
        async for i in gen:
            count += 1
            if count == 2:
                break

    t = asyncio.create_task(run_gen())
    await asyncio.sleep(0.01)
    event_bus.publish({"event_type": "test_event", "data": "test_data"})
    await t
