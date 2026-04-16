## 2024-05-24 — Unsafe Async Task Identification

Learning:
Generic hasattr(obj, "func") unwrapping to detect async closures inside WorkflowEngine can cause circular loops on malicious wrappers and false-positive crashes on completely valid class instances that simply have a .func() async method.

Action:
Always strictly check isinstance(obj, functools.partial) when unwrapping built-in wrappers. When evaluating custom closures or wrapped objects for asyncio properties, do not unwrap attributes based purely on naming convention unless you can securely verify the object type to prevent standard method masking.

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

## 2025-04-15 — Unwrapping functools.partial for callable async classes
Learning: When checking if a given function or class is an async coroutine (e.g. `hasattr(base_func, "__call__")` combined with `inspect.iscoroutinefunction()`), wrapped callables using `functools.partial` must be explicitly unwrapped first. A single unwrap or simply unwrapping `func` isn't enough; it should use `while isinstance(base_func, functools.partial): base_func = base_func.func`. Otherwise, wrapped async classes may be falsely identified as synchronous.
Action: Ensure any dynamic runtime introspection that checks for coroutine status safely unwraps `functools.partial` entirely before checking properties like `__call__`.