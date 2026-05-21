## 2026-05-06 — Memory Optimization / Reference Cycle

 Learning:
 Passing a shared mutable dictionary containing `asyncio.Task` objects directly into an inner coroutine creates a circular reference (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict). This prevents standard garbage collection and forces the GC to work harder to clean up the cycle.

 Action:
 Pass only pre-resolved lists of specific dependency tasks to execution 

 // ... truncated ... 

 dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
 Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.