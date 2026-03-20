## 2024-05-24 — Workflow Engine Parallel DAG Execution Bottleneck

Learning:
The core workflow engine implementation evaluated DAG execution generation by generation using `networkx.topological_generations()`. While it efficiently scheduled parallel tasks within the same topological level, it introduced a synchronization bottleneck: the next generation couldn't start until all tasks in the current generation completed, blocking independent tasks on slow neighbors in the same level.

Action:
Modified DAG execution logic to traverse the DAG directly, creating `asyncio.Task` wrappers for each node and orchestrating dependency resolution directly via `asyncio.gather` on the upstream dependencies. This allows tasks to execute truly in parallel without unnecessary synchronization barriers, improving throughput for uneven workflows.
