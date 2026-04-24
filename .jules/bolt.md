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

## 2024-04-17 — Fix asyncio.gather background task leak on BaseException

Learning:
When awaiting multiple tasks via `asyncio.gather()`, if one task raises a `BaseException` (like `SystemExit` or `KeyboardInterrupt`), the exception propagates immediately, but the remaining sibling tasks continue running as orphans in the background. This breaks cooperative task cancellation and can cause resource leaks or `RuntimeError: coroutine was never awaited`.

Action:
Wrap `asyncio.gather` in a `try...except BaseException` block. When caught, iterate over the task pool and `.cancel()` any tasks that are not yet `.done()`. Ensure they finish cancelling cleanly by awaiting them again with `return_exceptions=True` before re-raising the original exception.

## 2025-04-20 — Removing NetworkX dependency overhead

Learning:
Using a heavy third-party dependency like `networkx` solely for basic directed graph edge tracking and topological sorting introduces unnecessary bloat, larger memory footprints, and installation overhead, especially when targeting modern Python environments (>=3.9) which offer built-in alternatives.

Action:
Replaced `networkx` completely with the standard library `graphlib.TopologicalSorter`. Removed `nx.DiGraph` overhead in favor of maintaining a native `dict[str, list[str]]` for predecessors. Handled `graphlib.CycleError` in place of `nx.NetworkXUnfeasible`. This resulted in a cleaner runtime dependency tree and zero external package overhead for core DAG execution.

## 2024-04-22 — asyncio.as_completed memory leaks in fail-fast pattern

Learning:
When implementing a fail-fast mechanism (e.g., breaking out early from evaluating multiple dependent tasks), using `asyncio.as_completed` generates proxy iterators that yield un-awaited wrapper coroutines. If broken out of prematurely, these remaining un-awaited coroutines cause `RuntimeWarning: coroutine was never awaited` and memory leaks. Manually iterating over the generator to call `.close()` on them is brittle, unsafe in complex scenarios, and considered an anti-pattern.

Action:
Refactored the core execution path in `_run_node` to completely eliminate `asyncio.as_completed`. Replaced it with a cleaner `while pending_set:` loop using `asyncio.wait(pending_set, return_when=asyncio.FIRST_COMPLETED)`, which directly manages underlying tasks without spawning intermediate wrapper futures, thereby solving the memory leak safely and natively.

## 2024-04-24 — Workflow Engine DAG Execution Parallelism Simplification

Learning:
The `_run_node` fail-fast evaluation branch inside `WorkflowEngine` had an unnecessary and bloated inner logic chunk when tracking `pending_set` logic. The loop explicitly separated `done` and `pending_set` checks sequentially to bypass `asyncio.wait` for `len(pending_set) == 1`. By removing this custom manual queue logic and just letting `asyncio.wait` handle waiting on pending sets via `return_when=asyncio.FIRST_COMPLETED`, the codebase is vastly simpler and fewer corner cases pop up while keeping performance essentially identical since single dependency shortcuts still exist.

Action:
Removed the hand-crafted `pending_set.pop()` branch inside `WorkflowEngine._run_node` and simplified the collection strategy directly into `{tasks[dep] for dep in deps}` and passing them cleanly into `asyncio.wait`.
