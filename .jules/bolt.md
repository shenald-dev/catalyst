## 2025-04-04 — Closure Allocation in Hot Paths

Learning:
Defining inner functions (like `def _skip_result`) inside frequently executed hot paths (like `_run_node`) forces Python to allocate a new closure context on every invocation, causing unnecessary memory overhead and execution latency.

Action:
Refactored `_run_node` to track error state natively with a local variable (`failed_upstream: TaskError | None`) and consolidated the failure return at the end of the dependency evaluation block, eliminating the `_skip_result` closure entirely. Also modernized type hints from `typing.Dict`/`typing.List` to the built-in `dict`/`list`.
## 2025-04-06 — Topological Sort Caching

Learning:
`nx.topological_sort` performs a complete traversal of the graph (O(V+E)) on every execution, which is an unnecessary overhead for statically defined workflow DAGs that run repeatedly.

Action:
Introduced `_cached_topo_order` caching to `WorkflowEngine`. It pre-computes the topological order and caches it across `execute()` calls, invalidating only when a new task is added.
