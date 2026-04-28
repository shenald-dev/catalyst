## 2024-04-25 — Optimize DAG Execution Engine `_run_node` by replacing manual check loop with `asyncio.wait`

Learning:
In asynchronous programming with `asyncio`, doing manual checks like `if task.done(): res = task.result()` followed by `else: pending_set.add(task)` before using `asyncio.wait` introduces Python-level overhead and duplicates error-checking logic. `asyncio.wait` is implemented in C and can natively and safely evaluate sets of tasks, whether they are already complete or pending, handling the queue much more efficiently.

Action:
Always delegate state evaluation for sets of asyncio Futures/Tasks directly to `asyncio.wait` rather than pre-filtering or manual synchronous probing, eliminating redundant Python-level logic and keeping loops simpler and faster.

## 2024-05-18 — Prevent silent iterator exhaustion in workflow dependency registration

Learning:
When an API accepts an `Iterable` (like a generator) for a sequence parameter (e.g., `dependencies`), iterating over it during validation (like checking for missing tasks) will exhaust the iterator. If the same iterator is then used later in an assignment loop, the loop will silently do nothing because the iterator is already empty. This leads to missing data without raising any errors.

Action:
Always proactively materialize iterables into a concrete sequence (like `list(dependencies)`) immediately upon entering a function if the sequence needs to be iterated over multiple times (e.g., for validation followed by assignment). This prevents silent exhaustion bugs and creates a safe, defensive copy.
