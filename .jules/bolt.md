## 2024-05-24 — Workflow Engine Parallel DAG Execution Bottleneck

Learning:
The core workflow engine implementation evaluated DAG execution generation by generation using `networkx.topological_generations()`. While it efficiently scheduled parallel tasks within the same topological level, it introduced a synchronization bottleneck: the next generation couldn't start until all tasks in the current generation completed, blocking independent tasks on slow neighbors in the same level.

Action:
Modified DAG execution logic to traverse the DAG directly, creating `asyncio.Task` wrappers for each node and orchestrating dependency resolution directly via `asyncio.gather` on the upstream dependencies. This allows tasks to execute truly in parallel without unnecessary synchronization barriers, improving throughput for uneven workflows.

## 2024-05-25 — Workflow Engine Redundant DAG Validation and Inspection Overhead

Learning:
Two performance insights discovered in the workflow engine's core execution path:
1. `nx.is_directed_acyclic_graph(self.graph)` traverses the graph to check for cycles before calling `nx.topological_sort(self.graph)`, which also internally checks for cycles (and raises `nx.NetworkXUnfeasible`). Validating before sorting traverses the graph twice.
2. `inspect.iscoroutinefunction()` is relatively expensive to evaluate dynamically during task execution (`_run_task`), especially for workflows with many tasks.

Action:
1. Eliminated the explicit `nx.is_directed_acyclic_graph` check. Instead, wrapped the `nx.topological_sort` call in a `try/except` block, catching `nx.NetworkXUnfeasible`. This cuts the validation traversal overhead by half.
2. Moved the `inspect.iscoroutinefunction` check from execution time to registration time (`add_task()`), storing the boolean result to avoid introspection overhead in the hot path.

## 2024-05-26 — Workflow Engine Predecessor Lookup and Coroutine Creation Overhead

Learning:
Discovered two performance bottlenecks in the core `WorkflowEngine`:
1. `list(self.graph.predecessors(node))` queried the `networkx` graph dynamically on the hot path for every task node, which adds noticeable overhead during execution.
2. The inner `async def _execute()` closure within `_run_task` introduced unnecessary coroutine allocation and scheduling overhead for every executed task, even when timeouts were not required.

Action:
1. Eliminated the dynamic `networkx` predecessor queries by pre-computing dependencies directly into a standard Python dictionary `self._predecessors` during `add_task`.
2. Refactored `_run_task` to inline the task execution and timeout logic, removing the `_execute` closure, thereby directly awaiting the function or `asyncio.to_thread` for synchronous tasks, improving event loop efficiency.
