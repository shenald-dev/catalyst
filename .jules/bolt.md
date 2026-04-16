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

## 2024-04-16 — Refactored DAG engine execution hot paths for functional data flow

Learning:
Passing mutable dictionaries (like the `results` dict in `_run_node`) through asynchronous execution hot paths breaks functional data flow, creates tight coupling between scheduling and task execution, and can hinder performance and code maintainability by sharing unnecessary state.

Action:
Avoid passing mutable state dictionaries (like a shared `results` dict) through execution hot paths like `_run_node`. Instead, extract results directly via `task.result()` after task execution (e.g., within `execute()`) to maintain cleaner and more functional data flow.

## 2026-04-16 — Fix zombie dependency bug on overwritten tasks
Learning: When overwriting an existing task's dependencies using `WorkflowEngine.add_task()`, `NetworkX` does not automatically discard its previous incoming graph edges. This leaves the task topologically dependent on stale predecessors, potentially introducing execution order bugs and false cycles.
Action: explicitly remove existing incoming edges `self.graph.remove_edges_from(list(self.graph.in_edges(name)))` before updating a node in the internal directed graph structure.
