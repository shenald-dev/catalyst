import asyncio
import functools
import inspect
import logging
import networkx as nx
from typing import Any, Callable

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
        self.graph: nx.DiGraph[str] = nx.DiGraph()
        self.tasks: dict[str, Callable[..., Any]] = {}
        self._timeouts: dict[str, float | None] = {}
        self._is_async: dict[str, bool] = {}
        self._predecessors: dict[str, list[str]] = {}
        self._cached_topo_order: list[str] | None = None

    def add_task(
        self,
        name: str,
        func: Callable[..., Any],
        dependencies: list[str] | None = None,
        timeout: float | None = None,
    ) -> None:
        """Register a task and its dependencies.

        Args:
            name: Unique task identifier.
            func: Callable (sync or async) to execute.
            dependencies: List of task names this task depends on.
            timeout: Optional timeout in seconds. If the task exceeds this,
                     it is cancelled and recorded as a TaskError.

        Raises:
            ValueError: If a dependency references a task not yet registered.
        """
        # Validate dependencies exist before adding
        if dependencies:
            missing = [dep for dep in dependencies if dep not in self.tasks]
            if missing:
                raise ValueError(
                    f"Task {name!r} depends on unregistered tasks: {missing}"
                )
        self.graph.add_node(name)
        self._cached_topo_order = None
        self._predecessors[name] = []
        self.tasks[name] = func
        self._timeouts[name] = timeout
        base_func = func
        while isinstance(base_func, functools.partial):
            base_func = base_func.func

        self._is_async[name] = inspect.iscoroutinefunction(base_func) or (
            hasattr(base_func, "__call__")
            and inspect.iscoroutinefunction(base_func.__call__)
        )
        if dependencies:
            for dep in dependencies:
                self.graph.add_edge(dep, name)
                self._predecessors[name].append(dep)
        self._cached_topo_order = None

    async def _run_node(
        self,
        node: str,
        results: dict[str, Any],
        tasks: dict[str, asyncio.Task[Any]],
    ) -> Any:
        deps = self._predecessors.get(node, [])
        if deps:
            failed_upstream: TaskError | None = None
            if len(deps) == 1:
                res = await tasks[deps[0]]
                if isinstance(res, TaskError):
                    failed_upstream = res
            else:
                pending_set = set()
                for dep in deps:
                    t = tasks[dep]
                    if t.done():
                        res = t.result()
                        if isinstance(res, TaskError):
                            failed_upstream = res
                            break
                    else:
                        pending_set.add(t)

                if not failed_upstream and len(pending_set) == 1:
                    res = await pending_set.pop()
                    if isinstance(res, TaskError):
                        failed_upstream = res
                elif not failed_upstream and pending_set:
                    iterator = asyncio.as_completed(pending_set)
                    for f in iterator:
                        res = await f
                        if isinstance(res, TaskError):
                            failed_upstream = res
                            for remaining in iterator:
                                if hasattr(remaining, "close"):
                                    getattr(remaining, "close")()
                            break

            if failed_upstream is not None:
                res_err = TaskError(
                    node,
                    RuntimeError(
                        f"Skipped: upstream task {failed_upstream.task_name!r} failed"
                    ),
                )
                results[node] = res_err
                return res_err

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

            results[node] = result
            return result
        except Exception as e:
            logger.error("Task %r failed: %s", node, e)
            result = TaskError(node, e)
            results[node] = result
            return result

    async def execute(self) -> dict[str, Any]:
        """Execute the DAG in topological order, parallelizing independent tasks.

        Failed tasks produce TaskError results. Dependent tasks are skipped
        and also produce TaskErrors referencing the upstream failure.
        """
        if self._cached_topo_order is None:
            try:
                self._cached_topo_order = list(nx.topological_sort(self.graph))
            except nx.NetworkXUnfeasible:
                raise ValueError("Workflow must be a Directed Acyclic Graph (DAG)")

        results: dict[str, Any] = {}
        tasks: dict[str, asyncio.Task[Any]] = {}

        for node in self._cached_topo_order:
            tasks[node] = asyncio.create_task(self._run_node(node, results, tasks))

        if tasks:
            await asyncio.gather(*tasks.values())

        return results
