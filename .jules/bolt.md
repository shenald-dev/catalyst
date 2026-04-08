## 2025-04-07 — Optimize DAG topological sort evaluation

Learning:
The workflow engine evaluates `nx.topological_sort` on the DAG dynamically during each `execute()` call. For static workflows that are constructed once and executed repeatedly, this O(V+E) operation is unnecessary and adds overhead.

Action:
<<<<<<< Updated upstream
Refactored `_run_node` to track error state natively with a local variable (`failed_upstream: TaskError | None`) and consolidated the failure return at the end of the dependency evaluation block, eliminating the `_skip_result` closure entirely. Also modernized type hints from `typing.Dict`/`typing.List` to the built-in `dict`/`list`.

## 2026-04-07 — Topological Sort Recomputation Overhead

Learning:
For static DAGs executed repeatedly, recomputing `nx.topological_sort` on every `.execute()` call creates an O(V+E) performance penalty that compounds over multiple engine runs, especially for complex pipelines.

Action:
Cached the result of `nx.topological_sort` into `self._cached_topo_order` during engine instantiation and validated invalidation of the cache via `add_task()` when new tasks alter the DAG structure.
=======
Introduced a cache (`_cached_topo_order`) inside `WorkflowEngine` that computes and stores the sorted node order once. The cache is automatically invalidated when new tasks are added via `add_task`. This optimizes execution time on multiple workflow executions.
>>>>>>> Stashed changes
