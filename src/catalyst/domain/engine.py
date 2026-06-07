# src/catalyst/domain/engine.py
"""
Catalyst Domain Engine

This module provides the core execution engine for Catalyst workflows.
It exposes the following primitives for building and running directed acyclic graphs (DAGs) of tasks:

- `TaskError`: A structured representation of a failed task, containing the task name
  and the exception that caused the failure.
- `WorkflowEngine`: The core domain logic for parallel DAG execution. It handles task
  failures gracefully, ensuring that a failing task produces a `TaskError` result and
  dependent tasks are skipped rather than crashing the entire workflow.
"""
import asyncio
import functools
import inspect
import types
import logging
import graphlib
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)

__all__ = [
    "TaskError",
    "WorkflowEngine",
]


class TaskError:
    """Structured representation of a failed task."""

    __slots__ = ("task_name", "exception")

    def __init__(self, task_name: str, exception: BaseException) -> None:
        self.task_name = task_name
        self.exception = exception

    def __repr__(self) -> str:
        return f"TaskError({self.task_name!r}, {self.exception!r})"


class WorkflowEngine:
    """Core domain logic for parallel DAG execution.

    Handles task failures gracefully: a failing task produces a TaskError result,
    and dependent tasks are skipped (also producing TaskErrors) rather than
    crashing the entire workflow.
    """

    def __init__(self) -> None:
        self.tasks: dict[str, Callable[..., Any]] = {}
        self._timeouts: dict[str, float | None] = {}
        self._is_async: dict[str, bool] = {}
        self._predecessors: dict[str, list[str]] = {}
        self._cached_topo_order: list[str] | None = None

    def add_task(
        self,
        name: str,
        func: Callable[..., Any],
        dependencies: Iterable[str] | None = None,
        timeout: float | None = None,
    ) -> None:
        """Register a task and its dependencies.

        Args:
            name: Unique task identifier.
            func: Callable (sync or async) to execute.
            dependencies: Iterable of task names this task depends on.
            timeout: Optional timeout in seconds. If the task exceeds this,
                     it is cancelled and recorded as a TaskError.

        Raises:
            ValueError: If a dependency references a task not yet registered.
        """
        if dependencies is not None:
            # Convert dependencies to a list to prevent exhausting iterators/generators
            if isinstance(dependencies, str):
                dependencies = [dependencies]
            else:
                dependencies = list(dependencies)

        # Validate dependencies exist before adding
        if dependencies:
            missing = [dep for dep in dependencies if dep not in self.tasks]
            if missing:
                raise ValueError(
                    f"Task {name!r} depends on unregistered tasks: {missing}"
                )
        self.tasks[name] = func
        self._timeouts[name] = timeout

        # Check if the function is asynchronous, correctly unwrapping partials
        # and checking __call__ for async callable objects.
        is_async = inspect.iscoroutinefunction(func)
        if not is_async:
            base_func = func
            while isinstance(base_func, functools.partial):
                base_func = base_func.func
            # inspect.iscoroutinefunction naturally handles functions, methods, and builtins.
            # Only objects implementing __call__ might incorrectly return False.
            if not isinstance(base_func, types.FunctionType):
                is_async = inspect.iscoroutinefunction(base_func.__call__)
        
        self._is_async[name] = is_async
        self._predecessors[name] = dependencies or []
        self._cached_topo_order = None

    def _get_topo_order(self) -> list[str]:
        """Compute and cache the topological order of tasks."""
        if self._cached_topo_order is None:
            sorter = graphlib.TopologicalSorter(
                {name: self._predecessors[name] for name in self.tasks}
            )
            self._cached_topo_order = list(sorter.static_order())
        return self._cached_topo_order

    async def run(self, **kwargs: Any) -> dict[str, Any | TaskError]:
        """Execute the workflow and return results for all tasks.

        Args:
            **kwargs: Initial inputs or arguments for tasks without dependencies.

        Returns:
            A dictionary mapping task names to their results or TaskError instances.
        """
        results: dict[str, Any | TaskError] = {}
        topo_order = self._get_topo_order()

        for task_name in topo_order:
            func = self.tasks[task_name]
            deps = self._predecessors[task_name]
            
            # Check if any dependency failed
            dep_errors = [d for d in deps if isinstance(results.get(d), TaskError)]
            if dep_errors:
                results[task_name] = TaskError(
                    task_name, Exception(f"Dependency failed: {dep_errors}")
                )
                continue

            # Gather arguments
            args = {d: results[d] for d in deps}
            sig = inspect.signature(func)
            for k, v in kwargs.items():
                if k in sig.parameters:
                    args[k] = v

            try:
                timeout = self._timeouts[task_name]
                if self._is_async[task_name]:
                    if timeout:
                        results[task_name] = await asyncio.wait_for(
                            func(**args), timeout=timeout
                        )
                    else:
                        results[task_name] = await func(**args)
                else:
                    if timeout:
                        results[task_name] = await asyncio.wait_for(
                            asyncio.to_thread(func, **args), timeout=timeout
                        )
                    else:
                        results[task_name] = await asyncio.to_thread(func, **args)
            except asyncio.TimeoutError as e:
                results[task_name] = TaskError(task_name, e)
            except Exception as e:
                results[task_name] = TaskError(task_name, e)

        return results
