## 2024-04-25 — Optimize DAG Execution Engine `_run_node` by replacing manual check loop with `asyncio.wait`

   Learning:
   In asynchronous programming with `asyncio`, doing manual checks like `if task.done(): res = task.result()` followed by `else: pending_set.add(task)` before using `asyncio.wait` introduces Python-level overhead and duplicates error

   // ... 3353 characters truncated (middle section) ...

   ng asyncio.Task objects into a coroutine creates a memory-leaking reference cycle (dictionary -> Task -> Coroutine -> dictionary) in long-running parallel workflows.

   Action:
   Pass pre-resolved tuples of required tasks instead of mutable state dictionaries into execution hot paths to break the cycle without introducing synchronous list allocations.