## 2026-05-06 — Memory Optimization / Reference Cycle

Learning:
Passing a shared mutable dictionary containing `asyncio.Task` objects directly into an inner coroutine creates a circular reference (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict). This prevents standard garbage collection and forces the GC to work harder to clean up the cycle.

Action:
Pass only pre-resolved lists of specific dependency tasks to execution coroutines. Avoid passing the entire application task dictionary into individual nodes to maintain a functional data flow and break reference cycles automatically.

## 2024-04-25 — Optimize DAG Execution Engine `_run_node` by replacing manual check loop with `asyncio.wait`

Learning:
In asynchronous programming with `asyncio`, doing manual checks like `if task.done():

// ... 4157.2 characters truncated (middle section) ...

raded locked dependencies using `uv lock --upgrade` while explicitly constraining mypy<2.

## 2026-05-17 — Safe Dependency Upgrades

Learning:
Continuous dependency upgrades are essential for security and reliability, but strict static analysis tools like `mypy` should have their major versions constrained to prevent sudden CI breakage.

Action:
Upgraded locked dependencies using `uv lock --upgrade` while explicitly constraining mypy<2.

## 2026-05-20 — Error Observability & Logging Tracebacks

Learning:
When handling failures gracefully inside a DAG execution engine (where exceptions are caught and wrapped into `TaskError` objects rather than crashing the process), logging only `logger.error("... %s", e)` discards the stack traceback. This severely limits observability and forces developers to guess where the task actually failed inside their custom logic.

Action:
Inside `except` blocks dealing with arbitrary user-code failures, always use `logger.exception(...)` instead of `logger.error(...)`. This natively appends the full traceback to the application logs while still safely swallowing the exception at runtime to prevent process crashes.