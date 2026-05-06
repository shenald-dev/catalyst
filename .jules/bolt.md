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

## 2024-05-18 — Optimize inspect and list assignment overhead in task registration and fail-fast loops

Learning:
In highly concurrent DAG construction, repeated runtime type introspection (`isinstance` loops over `functools.partial`) on standard async functions adds significant CPU overhead. Additionally, managing error states via nested variable tracking (`failed_upstream = res; break` followed by `if failed_upstream: return TaskError(...)`) requires extra bytecode evaluation over a simpler direct return strategy. Finally, copying optional list inputs via manual loops or iterative list assignments can be simplified directly via `list(dependencies) if dependencies is not None else []`.

Action:
Always use a fast path condition (`inspect.iscoroutinefunction(func)`) before iterating through deep unwrapping logic to short-circuit introspection for standard functions. Use early returns (`return TaskError(...)`) in asynchronous fail-fast loops to bypass redundant state-tracking variables.

## 2026-05-01 — String Dependency Destructuring Bug

Learning:
When accepting an `Iterable` or generator for sequence parameters (like `dependencies`), explicitly check for strings first to avoid unintentionally exhausting or destructuring them. `list("task_a")` yields `['t', 'a', 's', 'k', '_', 'a']`, causing unregistered task `ValueError`s.

Action:
Always implement an explicit `isinstance(val, str)` check when normalizing iterables into lists to prevent strings from breaking expected behavior.
