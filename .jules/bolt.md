## 2024-05-18 — True Parallel Execution in DAG Workflow Engine

Learning:
The DAG execution engine `WorkflowEngine.execute` claimed to run independent tasks in parallel but was implemented using a simple sequential `for` loop over `nx.topological_sort`. This was a silent performance bottleneck where independent tasks were executing one-after-the-other instead of concurrently.

Action:
Modified `WorkflowEngine.execute` to use `nx.topological_generations` combined with `asyncio.gather`. This accurately groups tasks that can run in parallel (no dependencies on each other in the current generation) and awaits them concurrently before moving to the next generation, unlocking true async parallelism for independent DAG tasks.