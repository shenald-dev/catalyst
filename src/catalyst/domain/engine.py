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
            name: The unique identifier for the task.
            func: The callable to execute for this task.
            dependencies: An iterable of task names that must complete before this task runs.
            timeout: Optional timeout in seconds for the task execution.

        Raises:
            ValueError: If a task with the given name is already registered.
        """
        if name in self.tasks:
            raise ValueError(f"Task '{name}' is already registered.")
        
        self.tasks[name] = func
        self._timeouts[name] = timeout
        self._is_async[name] = asyncio.iscoroutinefunction(func)
        self._predecessors[name] = list(dependencies) if dependencies else []
        self._cached_topo_order = None

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the registered tasks in topological order.

        Args:
            **kwargs: Initial inputs or arguments to be passed to tasks without dependencies.

        Returns:
            A dictionary mapping task names to their results or `TaskError` instances.
        """
        if not self.tasks:
            return {}

        results: dict[str, Any] = {}
        graph = {name: set(deps) for name, deps in self._predecessors.items()}
        
        sorter = graphlib.TopologicalSorter(graph)
        sorter.prepare()
        
        while sorter.is_active():
            ready_tasks = tuple(sorter.get_ready())
            
            async def run_task(task_name: str) -> tuple[str, Any]:
                func = self.tasks[task_name]
                is_async = self._is_async[task_name]
                timeout = self._timeouts[task_name]
                
                task_kwargs = {}
                for pred in self._predecessors[task_name]:
                    pred_result = results.get(pred)
                    if isinstance(pred_result, TaskError):
                        return task_name, TaskError(
                            task_name, 
                            RuntimeError(f"Dependency '{pred}' failed: {pred_result.exception}")
                        )
                    task_kwargs[pred] = pred_result
                
                if not self._predecessors[task_name]:
                    task_kwargs.update(kwargs)
                
                try:
                    if is_async:
                        if timeout:
                            res = await asyncio.wait_for(func(**task_kwargs), timeout=timeout)
                        else:
                            res = await func(**task_kwargs)
                    else:
                        if timeout:
                            loop = asyncio.get_running_loop()
                            res = await asyncio.wait_for(
                                loop.run_in_executor(None, functools.partial(func, **task_kwargs)),
                                timeout=timeout
                            )
                        else:
                            res = func(**task_kwargs)
                    return task_name, res
                except Exception as e:
                    return task_name, TaskError(task_name, e)

            task_results = await asyncio.gather(*(run_task(t) for t in ready_tasks))
            
            for task_name, result in task_results:
                results[task_name] = result
                sorter.done(task_name)
                
        return results
