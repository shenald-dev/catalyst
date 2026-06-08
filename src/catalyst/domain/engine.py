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
    """Structured representation of a failed task.

    This class encapsulates the identity of the failed task and the specific
    exception that caused the failure, allowing the workflow engine to propagate
    errors gracefully without halting the entire execution graph.

    Attributes:
        task_name (str): The unique identifier of the task that failed.
        exception (BaseException): The exception instance raised during task execution.
    """

    __slots__ = ("task_name", "exception")

    def __init__(self, task_name: str, exception: BaseException) -> None:
        """Initialize a TaskError instance.

        Args:
            task_name: The unique identifier of the failed task.
            exception: The exception that caused the task to fail.
        """
        self.task_name = task_name
        self.exception = exception

    def __repr__(self) -> str:
        """Return a string representation of the TaskError."""
        return f"TaskError({self.task_name!r}, {self.exception!r})"


class WorkflowEngine:
    """Core domain logic for parallel DAG execution.

    The WorkflowEngine manages the registration, dependency resolution, and
    execution of tasks within a directed acyclic graph (DAG). It handles task
    failures gracefully: a failing task produces a `TaskError` result, and
    dependent tasks are skipped (also producing `TaskError`s) rather than
    crashing the entire workflow.

    Attributes:
        tasks: A mapping of task names to their corresponding callable functions.
    """

    def __init__(self) -> None:
        """Initialize a new WorkflowEngine instance."""
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
        """Register a task and its dependencies within the workflow.

        Args:
            name: A unique identifier for the task.
            func: The callable (synchronous or asynchronous) to execute.
            dependencies: An iterable of task names that this task depends on.
            timeout: An optional timeout in seconds. If the task execution exceeds
                     this duration, it is cancelled and recorded as a `TaskError`.

        Raises:
            ValueError: If any dependency references a task that has not yet been
                        registered with the engine.
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
        self._is_async[name] = inspect.iscoroutinefunction(func)
        self._predecessors[name] = list(dependencies) if dependencies else []
        self._cached_topo_order = None

    def _get_topological_order(self) -> list[str]:
        """Compute and cache the topological execution order of tasks.

        Returns:
            A list of task names ordered such that all dependencies of a task
            appear before the task itself.

        Raises:
            graphlib.CycleError: If the registered task dependencies contain a cycle.
        """
        if self._cached_topo_order is None:
            graph = {name: tuple(deps) for name, deps in self._predecessors.items()}
            sorter = graphlib.TopologicalSorter(graph)
            self._cached_topo_order = list(sorter.static_order())
        return self._cached_topo_order

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the registered workflow and return results for all tasks.

        Tasks are executed in topological order. If a task fails or times out,
        it is recorded as a `TaskError`, and all dependent tasks are automatically
        skipped and also recorded as `TaskError`s to prevent cascading failures.

        Args:
            **kwargs: Initial keyword arguments to pass to root tasks (tasks with
                      no dependencies).

        Returns:
            A dictionary mapping each task name to its execution result, or a
            `TaskError` instance if the task failed, timed out, or was skipped
            due to a dependency failure.
        """
        results: dict[str, Any] = {}
        topo_order = self._get_topological_order()

        for task_name in topo_order:
            func = self.tasks[task_name]
            deps = self._predecessors[task_name]

            # Check if any dependency resulted in a TaskError
            if any(isinstance(results.get(dep), TaskError) for dep in deps):
                results[task_name] = TaskError(
                    task_name,
                    RuntimeError("Skipped due to dependency failure")
                )
                continue

            # Prepare arguments for the task
            task_kwargs = {dep: results[dep] for dep in deps}
            if not deps:
                task_kwargs.update(kwargs)

            try:
                timeout = self._timeouts[task_name]
                if self._is_async[task_name]:
                    if timeout is not None:
                        results[task_name] = await asyncio.wait_for(
                            func(**task_kwargs), timeout=timeout
                        )
                    else:
                        results[task_name] = await func(**task_kwargs)
                else:
                    if timeout is not None:
                        results[task_name] = await asyncio.wait_for(
                            asyncio.to_thread(func, **task_kwargs), timeout=timeout
                        )
                    else:
                        # Run synchronous functions in a thread to avoid blocking the event loop
                        results[task_name] = await asyncio.to_thread(func, **task_kwargs)
            except asyncio.TimeoutError as e:
                logger.warning("Task %r timed out after %s seconds", task_name, timeout)
                results[task_name] = TaskError(task_name, e)
            except Exception as e:
                logger.exception("Task %r failed with exception", task_name)
                results[task_name] = TaskError(task_name, e)

        return results
