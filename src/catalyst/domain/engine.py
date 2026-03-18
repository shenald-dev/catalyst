import asyncio
import inspect
import logging
import networkx as nx
from typing import Any, Callable, Dict, List

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
        self.tasks: Dict[str, Callable[..., Any]] = {}
        self._timeouts: Dict[str, float | None] = {}

    def add_task(
        self,
        name: str,
        func: Callable[..., Any],
        dependencies: List[str] | None = None,
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
        self.tasks[name] = func
        self._timeouts[name] = timeout
        if dependencies:
            for dep in dependencies:
                self.graph.add_edge(dep, name)

    async def _run_task(self, name: str) -> Any:
        func = self.tasks[name]
        timeout = self._timeouts.get(name)

        async def _execute() -> Any:
            if inspect.iscoroutinefunction(func):
                return await func()
            # Run synchronous functions in a separate thread so they don't block the event loop
            return await asyncio.to_thread(func)

        if timeout is not None:
            return await asyncio.wait_for(_execute(), timeout=timeout)
        return await _execute()

    async def execute(self) -> Dict[str, Any]:
        """Execute the DAG in topological order, parallelizing independent tasks.

        Failed tasks produce TaskError results. Dependent tasks are skipped
        and also produce TaskErrors referencing the upstream failure.
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Workflow must be a Directed Acyclic Graph (DAG)")

        results: Dict[str, Any] = {}
        for generation in nx.topological_generations(self.graph):
            # Filter out tasks whose dependencies have failed
            runnable: List[str] = []
            skipped: List[str] = []
            for node in generation:
                deps = list(self.graph.predecessors(node))
                failed_deps = [d for d in deps if isinstance(results.get(d), TaskError)]
                if failed_deps:
                    skipped.append(node)
                    # Record skip with reference to first failed dependency
                    cause = results[failed_deps[0]]
                    results[node] = TaskError(
                        node,
                        RuntimeError(
                            f"Skipped: upstream task {cause.task_name!r} failed"
                        ),
                    )
                else:
                    runnable.append(node)

            if not runnable:
                continue

            # Run all runnable tasks in this generation concurrently, isolating failures
            generation_results = await asyncio.gather(
                *(self._run_task(node) for node in runnable),
                return_exceptions=True,
            )
            for node, result in zip(runnable, generation_results):
                if isinstance(result, BaseException):
                    logger.error("Task %r failed: %s", node, result)
                    results[node] = TaskError(node, result)
                else:
                    results[node] = result

        return results
