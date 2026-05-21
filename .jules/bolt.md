## 2026-05-06 — Memory Optimization / Reference Cycle

        Learning:
        Passing a shared mutable dictionary containing `asyncio.Task` objects directly into an inner coroutine creates a circular reference (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict). This prevents standard garbage collection and forces the GC to work harder to clean up the cycle.

        Action:
        Pass only pre-resolved lists of specific dependency tasks to execution coroutines. Avoid passing the entire application task dictionary into individual nodes to maintain a functional data flow and break reference cycles automatically.

        ## 2024-04-25 — Optimize DAG Execution Engine `_run_node` by replacing manual check loop with `asyncio.wait`

        Learning:
        In asynchronous programming with `asyncio`, doing manual checks like `if task.done(): res = task.result()` followed by `else: pending_set.add(task)` before using `asyncio.wait` introduces Python-level ove

        // ... 3200.6 characters truncated (middle section) ...

        applicable to avoid breaking observability and compatibility.

        2024-05-11 — DAG Execution Memory Optimization
        Learning: Passing a mutable dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
        Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.

        ## 2026-05-17 — Safe Dependency Upgrades

        Learning:
        Continuous dependency upgrades are essential for security and reliability, but strict static analysis tools like `mypy` should have their major versions constrained to prevent sudden CI breakage.

        Action:
        Upgraded locked dependencies using `uv lock --upgrade` while explicitly constraining mypy<2.