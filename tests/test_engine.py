import pytest
from catalyst.domain.engine import WorkflowEngine


@pytest.mark.asyncio
async def test_mixed_sync_async_execution() -> None:
    engine = WorkflowEngine()

    def sync_task() -> str:
        return "sync_result"

    async def async_task() -> str:
        return "async_result"

    engine.add_task("sync_task", sync_task)
    engine.add_task("async_task", async_task)

    results = await engine.execute()

    assert results == {"sync_task": "sync_result", "async_task": "async_result"}
