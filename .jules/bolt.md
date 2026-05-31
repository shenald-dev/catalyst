a mutable dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
           Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.
## 2026-05-06 — Memory Optimization / Reference Cycle

Learning:
Passing a shared mutable dictionary containing `asyncio.Task` objects directly into an inner coroutine creates a circular reference (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict). This prevents standard garbage collection and forces the GC to work harder to clean up the cycle.

Action:
Pass only pre-resolved lists of specific dependency tasks to execution coroutines. Avoid passing the entire application task dictionary into individual nodes to maintain a functional data flow and break reference cycles automatically.

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

## 2024-05-19 — Optimize unwrapping of functools.partial

Learning:
Exact type checking (`type(...) is functools.partial`) can provide a microscopic performance benefit over `isinstance()` during the unwrapping of tasks, but breaks inheritance and PEP 8 guidelines. However, memory explicitly dictated its use for unwrapping hot-paths.

Action:
Ensure strict type checking is isolated to paths where subclassing is intentionally non-applicable to avoid breaking observability and compatibility.

2024-05-11 — DAG Execution Memory Optimization
Learning: Passing a mutable dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.

## 2026-05-18 — FunctionType fast path for iscoroutinefunction

Learning: Calling `inspect.iscoroutinefunction(func.__call__)` is very slow when dealing with standard functions, because it searches the class hierarchy and raises/catches internal errors or searches the MRO. We can bypass this by checking if the object is a standard function, method, or builtin function type before attempting to introspect its `__call__` method.

Action: In hot paths where we check if an object is an async callable class by inspecting its `__call__` method, avoid doing so if the object is already known to be a standard function/method that `inspect.iscoroutinefunction(func)` would have already handled.

## 2026-05-17 — Safe Dependency Upgrades

Learning:
Continuous dependency upgrades are essential for security and reliability, but strict static analysis tools like `mypy` should have their major versions constrained to prevent sudden CI breakage.

Action:
Upgraded locked dependencies using `uv lock --upgrade` while explicitly constraining mypy<2.

## 2026-05-20 — Error Observability & Logging Tracebacks

Learning:
When handling failures gracefully inside a DAG execution engine (where exceptions are caught and wrapped into `TaskError` objects rather than crashing the process), logging only `logger.error("... %s", e)` discards the stack traceback. This severely limits observability and forces developers to guess where the task actually failed inside their custom logic.

Action:
Inside `except` blocks dealing with arbitrary user-code failures, always use `logger.exception(...)` instead of `logger.error(...)`. This natively appends the full traceback to the application logs while still safely swallowing the exception at runtime to prevent process crashes.
## 2026-05-13 — Do not remove explicit fast-paths for single dependencies

Learning: Removing `if len(dep_tasks) == 1:` and replacing it entirely with `asyncio.wait(set(dep_tasks))` introduces unnecessary overhead (set allocations, internal task management) for linear workflow chains, causing a performance regression. Also, consolidating state dictionaries while keeping the original creates duplicate state.

Action: Preserve explicit fast-path checks in hot loops (like DAG node execution). Do not consolidate internal state dictionaries into combined structures if original public-facing dictionaries must be maintained for backwards compatibility.
Inside `except` blocks dealing with arbitrary user-code failures, always use `logger.exception(...)` instead of `logger.error(...)`. This natively appends the full traceback to the application logs while still safely swallowing the exception at runtime to prevent process crashes.
