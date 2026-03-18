## 2024-05-18 — True Parallel Execution in DAG Workflow Engine

Learning:
The DAG execution engine `WorkflowEngine.execute` claimed to run independent tasks in parallel but was implemented using a simple sequential `for` loop over `nx.topological_sort`. This was a silent performance bottleneck where independent tasks were executing one-after-the-other instead of concurrently.

Action:
Modified `WorkflowEngine.execute` to use `nx.topological_generations` combined with `asyncio.gather`. This accurately groups tasks that can run in parallel (no dependencies on each other in the current generation) and awaits them concurrently before moving to the next generation, unlocking true async parallelism for independent DAG tasks.

## 2023-10-24 — Prevent sync tasks blocking event loop

Learning:
In the `WorkflowEngine` parallel execution, running a blocking synchronous task directly inside a coroutine blocks the entire `asyncio` event loop. This defeats the purpose of `asyncio.gather` for parallel node execution and freezes progress of other async tasks.

Action:
Always execute non-async functions using `await asyncio.to_thread(func)` in the core `_run_task` executor, so the sync function runs in a separate thread pool and the event loop can continue to process async tasks and unblock concurrent dependencies.
