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
## 2026-04-11 — Async Callable Resolution via functools.partial\nLearning:\nThe workflow engine used `inspect.iscoroutinefunction()` and `hasattr(base_func, '__call__')` checks dynamically on registered tasks to determine if a task is async. However, functions wrapped in `functools.partial` were not properly introspected because `iscoroutinefunction` returns `False` for a partial object of an async function. Using `.func` on partials directly isn't perfectly reliable unless evaluated repeatedly via `while isinstance(base_func, functools.partial)`.\nAction:\nUpdated the task registration phase in `WorkflowEngine.add_task` to recursively unwrap `functools.partial` objects and extract the `base_func` before checking the async signature. Added explicit unit tests for both async and sync callables wrapped in `functools.partial`.
