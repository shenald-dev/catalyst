import asyncio
import functools
import inspect
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

        is_async = False
        if inspect.iscoroutinefunction(func):
            is_async = True
        else:
            base_func = func
            while isinstance(base_func, functools.partial):
                base_func = base_func.func
            if inspect.iscoroutinefunction(base_func):
                is_async = True
            elif hasattr(base_func, "__call__") and inspect.iscoroutinefunction(
                base_func.__call__
            ):
                is_async = True

        self._is_async[name] = is_async
        self._predecessors[name] = (
            list(dependencies) if dependencies is not None else []
        )
        self._cached_topo_order = None

    async def _run_node(
        self,
        node: str,
        tasks: dict[str, asyncio.Task[Any]],
    ) -> Any:
        """Evaluate and execute a single node in the DAG.

        Uses a fast-path for single dependencies. For multiple dependencies,
        evaluates them safely using `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)`
        to implement clean fail-fast behavior without leaving un-awaited wrapper coroutines.
        """
        deps = self._predecessors.get(node, [])
        if deps:
            if len(deps) == 1:
                res = await tasks[deps[0]]
                if isinstance(res, TaskError):
                    return TaskError(
                        node,
                        RuntimeError(
                            f"Skipped: upstream task {res.task_name!r} failed"
                        ),
                    )
            else:
                pending_set = {tasks[dep] for dep in deps}

                while pending_set:
                    done, pending_set = await asyncio.wait(
                        pending_set, return_when=asyncio.FIRST_COMPLETED
                    )
                    for t in done:
                        res = t.result()
                        if isinstance(res, TaskError):
                            return TaskError(
                                node,
                                RuntimeError(
                                    f"Skipped: upstream task {res.task_name!r} failed"
                                ),
                            )

        try:
            func = self.tasks.get(node)
            if func is None:
                raise KeyError(f"Task {node!r} not found")
            timeout = self._timeouts.get(node)
            is_async = self._is_async.get(node, False)

            coro = func() if is_async else asyncio.to_thread(func)

            if timeout is not None:
                result = await asyncio.wait_for(coro, timeout=timeout)
            else:
                result = await coro

            return result
        except Exception as e:
            logger.error("Task %r failed: %s", node, e)
            return TaskError(node, e)

    async def execute(self) -> dict[str, Any]:
        """Execute the DAG in topological order, parallelizing independent tasks.

        Failed tasks produce TaskError results. Dependent tasks are skipped
        and also produce TaskErrors referencing the upstream failure.
        """
        if self._cached_topo_order is None:
            try:
                ts = graphlib.TopologicalSorter(self._predecessors)
                self._cached_topo_order = list(ts.static_order())
            except graphlib.CycleError:
                raise ValueError("Workflow must be a Directed Acyclic Graph (DAG)")

        tasks: dict[str, asyncio.Task[Any]] = {}

        for node in self._cached_topo_order:
            tasks[node] = asyncio.create_task(self._run_node(node, tasks))

        if tasks:
            try:
                await asyncio.gather(*tasks.values())
            except BaseException:
                for task in tasks.values():
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks.values(), return_exceptions=True)
                raise

        return {node: task.result() for node, task in tasks.items()}
