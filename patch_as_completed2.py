from catalyst.domain.engine import TaskError
import asyncio

async def test():
    class TaskErrorMock:
        def __init__(self, n, e):
            self.task_name = n
            self.exception = e

    tasks = {
        "A": asyncio.create_task(asyncio.sleep(0.5, "ok")),
        "B": asyncio.create_task(asyncio.sleep(0.1, TaskErrorMock("B", ValueError("err")))),
    }
    deps = ["A", "B"]
    results = {}

    for f in asyncio.as_completed([tasks[dep] for dep in deps]):
        res = await f
        if isinstance(res, TaskErrorMock):
            print(f"Skipped: upstream task {res.task_name!r} failed")

asyncio.run(test())
