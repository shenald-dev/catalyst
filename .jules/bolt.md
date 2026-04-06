## 2024-04-06 — Topological Sort Performance Bottleneck
Learning:
NetworkX's `topological_sort` is an O(V+E) operation. Executing it on every `.execute()` call inside a static DAG creates a severe and unnecessary performance bottleneck for pipelines that run repeatedly.
Action:
Always cache expensive graph topology evaluations. Invalidate the cache inside methods that mutate the graph structure (e.g., `add_task`), ensuring hot-paths can pull the evaluation instantly in constant time.
