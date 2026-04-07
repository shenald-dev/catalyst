## 2025-04-07 — Optimize DAG topological sort evaluation

Learning:
The workflow engine evaluates `nx.topological_sort` on the DAG dynamically during each `execute()` call. For static workflows that are constructed once and executed repeatedly, this O(V+E) operation is unnecessary and adds overhead.

Action:
Introduced a cache (`_cached_topo_order`) inside `WorkflowEngine` that computes and stores the sorted node order once. The cache is automatically invalidated when new tasks are added via `add_task`. This optimizes execution time on multiple workflow executions.
