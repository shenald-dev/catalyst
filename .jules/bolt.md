## 2025-04-04 — Closure Allocation in Hot Paths

Learning:
Defining inner functions (like `def _skip_result`) inside frequently executed hot paths (like `_run_node`) forces Python to allocate a new closure context on every invocation, causing unnecessary memory overhead and execution latency.

Action:
Refactored `_run_node` to track error state natively with a local variable (`failed_upstream: TaskError | None`) and consolidated the failure return at the end of the dependency evaluation block, eliminating the `_skip_result` closure entirely. Also modernized type hints from `typing.Dict`/`typing.List` to the built-in `dict`/`list`.

## 2026-04-07 — Topological Sort Recomputation Overhead

Learning:
For static DAGs executed repeatedly, recomputing `nx.topological_sort` on every `.execute()` call creates an O(V+E) performance penalty that compounds over multiple engine runs, especially for complex pipelines.

Action:
Cached the result of `nx.topological_sort` into `self._cached_topo_order` during engine instantiation and validated invalidation of the cache via `add_task()` when new tasks alter the DAG structure.

## 2025-04-08 — asyncio.as_completed Coroutine Leaks

Learning:
When breaking out of an `asyncio.as_completed` generator prematurely (e.g. during a fail-fast early return), Python leaves the remaining `_wait_for_one` coroutines un-awaited. This triggers `RuntimeWarning: coroutine was never awaited` during garbage collection and causes task references to leak.

Action:
Refactored `_run_node` to safely extract and exhaust the remaining `asyncio.as_completed` coroutines, explicitly closing them via `getattr(remaining, "close")()` to silence type checker warnings while guaranteeing clean object cleanup.

## 2026-04-09 — Async Callable Identification in Wrapping Decorators

Learning:
When utilizing decorators like `functools.partial` or custom callable classes, checking for coroutines purely via `inspect.iscoroutinefunction()` or `__call__` evaluation fails to identify the underlying async function, treating it as a standard synchronous function and throwing it off to `asyncio.to_thread`. This results in `RuntimeWarning: coroutine was never awaited`.

Action:
Updated the initialization routing of `WorkflowEngine.add_task` to natively trace function encapsulation via the `.func` property loop before evaluating `inspect.iscoroutinefunction`. Nested callables like `.partial` are correctly unwrapped, accurately identified, and securely executed asynchronously.
