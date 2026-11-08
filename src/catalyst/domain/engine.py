import asyncio
import functools
import graphlib
import inspect
import logging
import random
import time
import types
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class TaskError:
    """Structured representation of a failed task."""

    __slots__ = ("exception", "task_name")

    def __init__(self, task_name: str, exception: BaseException) -> None:
        self.task_name = task_name
        self.exception = exception

    def __repr__(self) -> str:
        return f"TaskError({self.task_name!r}, {self.exception!r})"


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration for automatic retry on task failure."""

    max_retries: int = 3
    delay: float = 0.05
    backoff: float = 2.0
    jitter: bool = True
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,)


@dataclass(slots=True)
class TaskMetrics:
    """Telemetry metrics captured during task execution."""

    task_name: str
    status: str  # "success", "failed", "skipped"
    start_time: float | None = None
    end_time: float | None = None
    duration_ms: float = 0.0
    retries_count: int = 0
    error: str | None = None


@dataclass
class WorkflowEvent:
    """Event emitted across workflow lifecycle."""

    event_type: str
    task_name: str | None = None
    data: Any = None
    timestamp: float = 0.0


class WorkflowResult(dict[str, Any]):
    """Enriched workflow result dictionary providing full dict backward-compatibility
    alongside execution telemetry and metrics.
    """

    def __init__(
        self,
        results: dict[str, Any],
        task_metrics: dict[str, TaskMetrics] | None = None,
        total_duration_ms: float = 0.0,
        status: str = "success",
    ) -> None:
        super().__init__(results)
        self.task_metrics: dict[str, TaskMetrics] = task_metrics or {}
        self.total_duration_ms: float = total_duration_ms
        self.status: str = status

    def to_dict(self) -> dict[str, Any]:
        """Convert results and metrics into a JSON-serializable dictionary."""
        return {
            "status": self.status,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "results": {
                k: {"error": str(v.exception), "task_name": v.task_name}
                if isinstance(v, TaskError)
                else v
                for k, v in self.items()
            },
            "task_metrics": {
                k: {
                    "task_name": m.task_name,
                    "status": m.status,
                    "duration_ms": round(m.duration_ms, 2),
                    "retries_count": m.retries_count,
                    "error": m.error,
                }
                for k, m in self.task_metrics.items()
            },
        }


@functools.lru_cache(maxsize=1024)
def _get_signature_cached(func: Callable[..., Any]) -> inspect.Signature | None:
    try:
        return inspect.signature(func)
    except (ValueError, TypeError):
        return None


def _get_signature(func: Callable[..., Any]) -> inspect.Signature | None:
    try:
        return _get_signature_cached(func)
    except TypeError:
        # Fallback for unhashable types (e.g., dynamically generated instances missing __hash__)
        try:
            return inspect.signature(func)
        except (ValueError, TypeError):
            return None


def _resolve_call_args(
    func: Callable[..., Any],
    dependencies: list[str],
    upstream_results: dict[str, Any],
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Determine args and kwargs to inject into func based on signature and upstream results."""
    sig = _get_signature(func)
    if sig is None:
        return (), {}

    params = sig.parameters
    if not params:
        return (), {}

    args: list[Any] = []
    kwargs: dict[str, Any] = {}

    has_var_positional = any(
        p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values()
    )

    mapped_deps = set()

    for p_name, p in params.items():
        if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            if p_name in upstream_results:
                if p.kind == inspect.Parameter.POSITIONAL_ONLY or (
                    has_var_positional
                    and p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                ):
                    args.append(upstream_results[p_name])
                else:
                    kwargs[p_name] = upstream_results[p_name]
                mapped_deps.add(p_name)
            elif p_name in ("context", "inputs", "upstream"):
                val = {
                    dep: upstream_results[dep]
                    for dep in dependencies
                    if dep in upstream_results
                }
                if p.kind == inspect.Parameter.POSITIONAL_ONLY or (
                    has_var_positional
                    and p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                ):
                    args.append(val)
                else:
                    kwargs[p_name] = val

    # If func accepts a single positional argument and wasn't matched by name
    if (
        len(params) == 1
        and len(dependencies) == 1
        and not kwargs
        and not args
        and not has_var_positional
    ):
        dep_name = dependencies[0]
        if dep_name in upstream_results:
            args.append(upstream_results[dep_name])
    elif has_var_positional:
        for dep in dependencies:
            if dep in upstream_results and dep not in mapped_deps:
                args.append(upstream_results[dep])

    return tuple(args), kwargs


class WorkflowEngine:
    """Core domain logic for parallel DAG execution.

    Handles task failures gracefully: a failing task produces a TaskError result,
    and dependent tasks are skipped (also producing TaskErrors) rather than
    crashing the entire workflow.
    """

    def __init__(self, max_concurrency: int | None = None) -> None:
        self.tasks: dict[str, Callable[..., Any]] = {}
        self._timeouts: dict[str, float | None] = {}
        self._retry_policies: dict[str, RetryPolicy | None] = {}
        self._is_async: dict[str, bool] = {}
        self._predecessors: dict[str, list[str]] = {}
        self._cached_topo_order: list[str] | None = None
        self._listeners: list[Callable[[WorkflowEvent], Any]] = []
        self._current_tasks: dict[str, asyncio.Task[Any]] | None = None
        self._current_metrics: dict[str, TaskMetrics] | None = None
        self.max_concurrency: int | None = max_concurrency
        self._semaphore: asyncio.Semaphore | None = None

    def add_listener(self, listener: Callable[[WorkflowEvent], Any]) -> None:
        """Register a callback for real-time lifecycle events."""
        self._listeners.append(listener)

    def _emit_event(
        self, event_type: str, task_name: str | None = None, data: Any = None
    ) -> None:
        """Broadcast an event to registered listeners."""
        if not self._listeners:
            return
        event = WorkflowEvent(
            event_type=event_type,
            task_name=task_name,
            data=data,
            timestamp=time.time(),
        )
        for listener in self._listeners:
            try:
                res = listener(event)
                if inspect.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as e:  # noqa: BLE001
                logger.warning("Event listener failed: %s", e)

    def add_task(
        self,
        name: str,
        func: Callable[..., Any],
        dependencies: Iterable[str] | None = None,
        timeout: float | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Register a task and its dependencies.

        Args:
            name: Unique task identifier.
            func: Callable (sync or async) to execute.
            dependencies: Iterable of task names this task depends on.
            timeout: Optional timeout in seconds. If the task exceeds this,
                     it is cancelled and recorded as a TaskError.
            retry_policy: Optional RetryPolicy to re-attempt execution upon failure.

        Raises:
            ValueError: If a dependency references a task not yet registered.
        """
        if dependencies is not None:
            # Convert dependencies to a list and deduplicate preserving order
            if isinstance(dependencies, str):
                dependencies = [dependencies]
            else:
                dependencies = list(dict.fromkeys(dependencies))

        # Validate dependencies exist before adding
        if dependencies:
            missing = [dep for dep in dependencies if dep not in self.tasks]
            if missing:
                raise ValueError(
                    f"Task {name!r} depends on unregistered tasks: {missing}"
                )
        self.tasks[name] = func
        self._timeouts[name] = timeout
        self._retry_policies[name] = retry_policy

        is_async = inspect.iscoroutinefunction(func)
        if not is_async:
            base_func = func
            while isinstance(base_func, functools.partial):
                base_func = base_func.func
            if (
                not isinstance(
                    base_func,
                    (types.FunctionType, types.MethodType, types.BuiltinFunctionType),
                )
                and callable(base_func)
                and inspect.iscoroutinefunction(
                    base_func.__call__  # type: ignore[operator]
                )
            ):
                is_async = True

        self._is_async[name] = is_async
        self._predecessors[name] = dependencies if dependencies is not None else []
        self._cached_topo_order = None

    def task(
        self,
        name: str | None = None,
        dependencies: Iterable[str] | None = None,
        timeout: float | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a task on this workflow engine."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            task_name = name or func.__name__
            self.add_task(
                name=task_name,
                func=func,
                dependencies=dependencies,
                timeout=timeout,
                retry_policy=retry_policy,
            )
            return func

        return decorator

    async def _run_node(
        self,
        node: str,
        dep_tasks: tuple[asyncio.Task[Any], ...],
    ) -> Any:
        """Evaluate and execute a single node in the DAG.

        Uses a fast-path for single dependencies. For multiple dependencies,
        evaluates them safely using event-driven dependency resolution to implement
        clean fail-fast behavior without leaving un-awaited wrapper coroutines.
        """
        metrics = (
            self._current_metrics.get(node)
            if self._current_metrics is not None
            else None
        )
        if dep_tasks:
            if len(dep_tasks) == 1:
                t = dep_tasks[0]
                try:
                    res = await asyncio.shield(t)
                except asyncio.CancelledError:
                    if not t.cancelled():
                        raise
                    try:
                        res = t.result()  # pragma: no cover
                    except asyncio.CancelledError as e:
                        res = TaskError(t.get_name(), e)
                if isinstance(res, TaskError):
                    if metrics:
                        metrics.status = "skipped"
                        metrics.error = f"Upstream task {res.task_name!r} failed"
                    self._emit_event(
                        "task_skipped",
                        node,
                        {"reason": f"upstream task {res.task_name!r} failed"},
                    )
                    return TaskError(
                        node,
                        RuntimeError(
                            f"Skipped: upstream task {res.task_name!r} failed"
                        ),
                    )
            else:
                loop = asyncio.get_running_loop()
                fut: asyncio.Future[Any] = loop.create_future()
                pending_count = len(dep_tasks)

                def _on_dep_done(t: asyncio.Task[Any]) -> None:
                    nonlocal pending_count
                    if fut.done():  # pragma: no cover
                        return
                    try:
                        res = t.result()
                    except asyncio.CancelledError as e:
                        res = TaskError(t.get_name(), e)
                    except BaseException as e:  # noqa: BLE001 # pragma: no cover
                        fut.set_exception(e)
                        return

                    if isinstance(res, TaskError):
                        fut.set_result(res)
                        return

                    pending_count -= 1
                    if pending_count == 0:
                        fut.set_result(None)

                for t in dep_tasks:
                    if fut.done():
                        break
                    if t.done():
                        _on_dep_done(t)
                    else:
                        t.add_done_callback(_on_dep_done)

                try:
                    res = await fut
                    if isinstance(res, TaskError):
                        if metrics:
                            metrics.status = "skipped"
                            metrics.error = f"Upstream task {res.task_name!r} failed"
                        self._emit_event(
                            "task_skipped",
                            node,
                            {"reason": f"upstream task {res.task_name!r} failed"},
                        )
                        return TaskError(
                            node,
                            RuntimeError(
                                f"Skipped: upstream task {res.task_name!r} failed"
                            ),
                        )
                finally:
                    for t in dep_tasks:
                        t.remove_done_callback(_on_dep_done)

        start_time = time.perf_counter()
        if metrics:
            metrics.start_time = start_time
            metrics.status = "running"
        if self._listeners:
            self._emit_event("task_started", node)

        try:
            if (func := self.tasks.get(node)) is None:
                raise KeyError(f"Task {node!r} not found")

            timeout = self._timeouts.get(node)
            is_async = self._is_async.get(node, False)
            retry_policy = self._retry_policies.get(node)

            # Build upstream results dictionary for data injection
            deps = self._predecessors.get(node, [])
            upstream_results: dict[str, Any] = {}
            if deps:
                for dep, dep_task in zip(deps, dep_tasks):
                    if dep_task.done():
                        dep_res = dep_task.result()
                        if not isinstance(dep_res, TaskError):
                            upstream_results[dep] = dep_res

            call_args, call_kwargs = _resolve_call_args(func, deps, upstream_results)

            max_attempts = (retry_policy.max_retries + 1) if retry_policy else 1
            attempt = 0
            last_err: Exception | None = None

            while attempt < max_attempts:
                attempt += 1
                try:

                    async def _execute_task() -> Any:
                        if is_async:
                            coro = func(*call_args, **call_kwargs)
                        else:
                            coro = asyncio.to_thread(func, *call_args, **call_kwargs)

                        if timeout is not None:
                            return await asyncio.wait_for(coro, timeout=timeout)
                        return await coro

                    if self._semaphore is not None:
                        async with self._semaphore:
                            result = await _execute_task()
                    else:
                        result = await _execute_task()

                    end_time = time.perf_counter()
                    if metrics:
                        metrics.end_time = end_time
                        metrics.duration_ms = (end_time - start_time) * 1000.0
                        metrics.status = "success"
                    if self._listeners:
                        self._emit_event("task_completed", node, {"result": result})
                    return result

                except Exception as exc:  # noqa: BLE001
                    last_err = exc
                    if (
                        attempt < max_attempts
                        and retry_policy
                        and isinstance(exc, retry_policy.retry_exceptions)
                    ):
                        if metrics:
                            metrics.retries_count += 1
                        delay = retry_policy.delay * (
                            retry_policy.backoff ** (attempt - 1)
                        )
                        if retry_policy.jitter:
                            delay *= random.uniform(0.75, 1.25)
                        self._emit_event(
                            "task_retrying",
                            node,
                            {
                                "attempt": attempt,
                                "error": str(exc),
                                "next_delay": delay,
                            },
                        )
                        await asyncio.sleep(delay)
                        continue
                    break

            assert last_err is not None
            raise last_err

        except Exception as e:
            end_time = time.perf_counter()
            if metrics:
                metrics.end_time = end_time
                metrics.duration_ms = (end_time - start_time) * 1000.0
                metrics.status = "failed"
                metrics.error = str(e)
            logger.exception("Task %r failed", node)
            if self._listeners:
                self._emit_event("task_failed", node, {"error": str(e)})
            return TaskError(node, e)

    async def execute(self) -> WorkflowResult:
        """Execute the DAG in topological order, parallelizing independent tasks.

        Failed tasks produce TaskError results. Dependent tasks are skipped
        and also produce TaskErrors referencing the upstream failure.
        """
        start_time = time.perf_counter()
        if self._cached_topo_order is None:
            try:
                ts = graphlib.TopologicalSorter(self._predecessors)
                self._cached_topo_order = list(ts.static_order())
            except graphlib.CycleError:
                raise ValueError("Workflow must be a Directed Acyclic Graph (DAG)")

        if self.max_concurrency is not None and self.max_concurrency > 0:
            self._semaphore = asyncio.Semaphore(self.max_concurrency)
        else:
            self._semaphore = None

        if self._listeners:
            self._emit_event(
                "workflow_started", data={"tasks": list(self.tasks.keys())}
            )

        tasks: dict[str, asyncio.Task[Any]] = {}
        task_metrics: dict[str, TaskMetrics] = {
            node: TaskMetrics(task_name=node, status="pending")
            for node in self._cached_topo_order
        }
        self._current_tasks = tasks
        self._current_metrics = task_metrics

        for node in self._cached_topo_order:
            deps = self._predecessors.get(node, [])
            dep_tasks = tuple(tasks[dep] for dep in deps) if deps else ()
            tasks[node] = asyncio.create_task(
                self._run_node(node, dep_tasks),
                name=node,
            )

        if tasks:
            try:
                await asyncio.gather(*tasks.values(), return_exceptions=True)
            except BaseException:
                self._current_tasks = None
                self._current_metrics = None
                for task in tasks.values():
                    task.cancel()
                await asyncio.gather(*tasks.values(), return_exceptions=True)
                raise

        end_time = time.perf_counter()
        total_duration_ms = (end_time - start_time) * 1000.0

        raw_results = {}
        for node, task in tasks.items():
            try:
                raw_results[node] = task.result()
            except asyncio.CancelledError as e:
                raw_results[node] = TaskError(node, e)

        has_failure = any(isinstance(v, TaskError) for v in raw_results.values())
        overall_status = "failure" if has_failure else "success"

        if self._listeners:
            self._emit_event(
                "workflow_completed",
                data={
                    "status": overall_status,
                    "duration_ms": total_duration_ms,
                },
            )

        result_obj = WorkflowResult(
            results=raw_results,
            task_metrics=task_metrics,
            total_duration_ms=total_duration_ms,
            status=overall_status,
        )
        self._current_tasks = None
        self._current_metrics = None
        return result_obj

    async def run(self, **_kwargs: Any) -> WorkflowResult:
        """Alias for execute() to maintain compatibility."""
        return await self.execute()
