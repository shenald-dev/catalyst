a mutable dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
           Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.
## 2026-05-06 — Memory Optimization / Reference Cycle

Learning:
Passing a shared mutable dictionary containing `asyncio.Task` objects directly into an inner coroutine creates a circular reference (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict). This prevents standard garbage collection and forces the GC to work harder to clean up the cycle.

Action:
Pass only pre-resolved lists of specific dependency tasks to execution coroutines. Avoid passing the entire application task dictionary into individual nodes to maintain a functional data flow and break reference cycles automatically.

## 2024-04-25 — Optimize DAG Execution Engine `_run_node` by replacing manual check loop with `asyncio.wait`

Learning:
In asynchronous programming wi

// ... 3287 characters truncated (middle section) ...


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

## 2024-05-19 — Resolve memory leak / reference cycle in _run_node

Learning:
Passing a dictionary of `asyncio.Task` objects into a coroutine creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).

Action:
Instead, pass a pre-resolved, highly efficient tuple of specific dependency tasks (e.g., `tuple(tasks[d] for d in deps)`) to the coroutine to break the cycle without introducing synchronous list/set allocations.
2024-05-11 — DAG Execution Memory Optimization
Learning: Passing a mutable dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.
2024-05-11 — DAG Execution Memory Optimization
Learning: Passing a mutable dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.
## 2024-05-07 — Optimize Memory Cycles and Partial Type Checks

Learning:
Passing a full dictionary of asyncio.Task objects into a task execution coroutine creates a memory-leaking reference cycle (tasks dict -> Task object -> Coroutine -> tasks dict). Additionally, exact type checking (e.g. `type(func) is functools.partial`) is brittle and breaks inheritance logic; standard `isinstance` is preferred.

Action:
## 2024-05-07 — Optimize Memory Cycles and Partial Type Checks

Learning:
Passing a full dictionary of asyncio.Task objects into a task execution coroutine creates a memory-leaking reference cycle (tasks dict -> Task object -> Coroutine -> tasks dict). Additionally, exact type checking (e.g. `type(func) is functools.partial`) is brittle and breaks inheritance logic; standard `isinstance` is preferred.

Action:
Refactored `_run_node` to break the memory reference cycle by explicitly passing only a list of needed dependency tasks (`dep_tasks`) rather than the entire execution dictionary. Updated type checks for partial unwrapping to use `isinstance` for robustness without sacrificing performance.
2024-05-11 — DAG Execution Memory Optimization
Learning: Passing a mutable dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.
## 2024-06-10 — Eliminate asyncio.Task Reference Cycles in execution engines

Learning:
Passing a full dictionary of running `asyncio.Task` objects down into nested coroutines (like a DAG node executor) causes each spawned coroutine to hold a reference to the entire collection of all tasks. This creates massive memory-leaking reference cycles (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).

Action:
Pre-resolve dependencies directly in the loop that spawns the tasks. Pass highly efficient sequences (e.g., tuples like `dep_tasks = tuple(tasks[d] for d in deps)`) into the coroutine rather than the whole registry dictionary. This cleanly breaks the reference cycle and completely avoids dictionary lookups inside the hot-path async execution context without adding new synchronous allocation overhead.
## 2024-05-11 — Memory optimization in DAG execution loop

Learning:
Passing a mutable dictionary of all running `asyncio.Task` objects into a coroutine (like a node execution function in a DAG engine) creates a memory-leaking reference cycle: the dictionary references the task, the task executes the coroutine, and the coroutine closure captures the dictionary.

Action:
Instead of passing the entire task state dictionary through the execution hot path, pre-resolve dependency tasks into a static, highly efficient tuple (e.g., `tuple(tasks[d] for d in deps)`) before executing the coroutine. This breaks the reference cycle, prevents memory leaks, and avoids additional synchronous allocations.
## 2024-05-10 — Prevent Memory Leaks via Reference Cycles in DAG Node Execution

Learning:
Passing a mutable state dictionary (like the `tasks` dict mapping task names to `asyncio.Task` objects) deep into execution hot paths, specifically as an argument to the coroutine that is stored *within* that dictionary, creates a significant reference cycle memory leak (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict) that the garbage collector struggles to clean up rapidly under heavy DAG execution load.

Action:
Break reference cycles in node execution by extracting pre-resolved, immutable, and highly efficient structures (like a `tuple` of specific dependent `Task` objects) before passing them into the coroutine context.
2024-05-11 — DAG Execution Memory Optimization
Learning: Passing a mutable dictionary of `asyncio.Task` objects through execution hot paths (like `_run_node`) creates a memory-leaking reference cycle (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict).
Action: Use pre-resolved tuples (e.g., `tuple(tasks[dep] for dep in deps)`) for dependencies when evaluating nodes. This isolates the references safely, prevents the cycle, and marginally improves hot path performance by reducing dictionary lookups.


## 2026-05-15 — Performance Optimizations in Workflow Engine

 Learning:
 We optimized engine execution by using generator expressions with empty fallback fast-paths (`tuple(x for x in y) if y else ()`) to avoid tuple memory allocations, and using the walrus operator (`:=`) to combine dictionary `get` lookups and validation.

 Action:
 In hot path execution graphs, use `tuple(tasks[d] for d in deps) if deps else ()` to bypass generator allocations for edge nodes entirely. Combine dictionary lookups with the walrus operator to avoid double-lookups or KeyError risks.
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

2026-05-29 — Memory leak via cyclic task dictionary in asyncio DAG

Learning:
Passing a mutable dictionary containing asyncio.Task objects into a coroutine creates a memory-leaking reference cycle (dictionary -> Task -> Coroutine -> dictionary) in long-running parallel workflows.

Action:
Pass pre-resolved tuples of required tasks instead of mutable state dictionaries into execution hot paths to break the cycle without introducing synchronous list allocations.
## 2026-05-13 — Do not remove explicit fast-paths for single dependencies

Learning: Removing `if len(dep_tasks) == 1:` and replacing it entirely with `asyncio.wait(set(dep_tasks))` introduces unnecessary overhead (set allocations, internal task management) for linear workflow chains, causing a performance regression. Also, consolidating state dictionaries while keeping the original creates duplicate state.

Action: Preserve explicit fast-path checks in hot loops (like DAG node execution). Do not consolidate internal state dictionaries into combined structures if original public-facing dictionaries must be maintained for backwards compatibility.
Inside `except` blocks dealing with arbitrary user-code failures, always use `logger.exception(...)` instead of `logger.error(...)`. This natively appends the full traceback to the application logs while still safely swallowing the exception at runtime to prevent process crashes.
