import asyncio
import functools
import inspect
import types
import logging
import graphlib
from typing import Any, Callable, Iterable

logger = logging.getLogger(__name__)


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

        is_async = inspect.iscoroutinefunction(func)
        if not is_async:
            base_func = func
            # Use exact type checking for performance. Subclasses of partial
            # are not supported in task execution hot paths.
            while type(base_func) is functools.partial:
                base_func = base_func.func
            if not isinstance(
                base_func,
                (types.FunctionType, types.MethodType, types.BuiltinFunctionType),
            ):
                if hasattr(base_func, "__call__") and inspect.iscoroutinefunction(
                    base_func.__call__
                ):
                    is_async = True
        if tasks:
            try:
                await asyncio.gather(*tasks.values())
            except BaseException:
                for task in tasks.values():
                    task.cancel()
                await asyncio.gather(*tasks.values(), return_exceptions=True)
                raise

        return {node: task.result() for node, task in tasks.items()}
