"""
Catalyst Core: High-performance task orchestration.
"""
import asyncio
import inspect
import time
import uuid
import importlib
import os
import subprocess
import sys
import warnings
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Any, Optional
from core.dag import DAG, DAGError
from core.plugin import PluginManager


def _maybe_use_uvloop():
    """If uvloop is installed and use_uvloop enabled, replace event loop policy."""
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    name: str
    func: Callable = None
    args: tuple = ()
    kwargs: Dict = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    plugin_name: str = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    duration: float = 0.0


class Orchestrator:
    """
    High-performance workflow orchestrator with DAG-based dependency resolution
    and a flexible plugin system.

    Phase 2 Enhancements:
    - Resource-aware scheduling (cpu, memory, io)
    - Per-task timeout and retry with exponential backoff
    - Cancellation propagation on failure
    - Optional OpenTelemetry tracing
    """

    def __init__(self, resource_limits: Optional[Dict[str, float]] = None,
                 enable_cancellation_propagation: bool = True,
                 enable_tracing: bool = False,
                 use_uvloop: bool = False,
                 tracer_provider = None,
                 otlp_endpoint: Optional[str] = None,
                 otlp_headers: Optional[Dict[str, str]] = None,
                 otlp_insecure: bool = False,
                 enable_profiling: bool = False,
                 profile_output: Optional[str] = None,
                 enable_metrics: bool = False,
                 metrics_port: Optional[int] = None):
        """
        Initialize the orchestrator.

        Args:
            resource_limits: Maximum available resources (e.g., {"cpu": 4.0, "memory_mb": 8192})
                             If None, resource limits are not enforced.
            enable_cancellation_propagation: If True, task failures cancel downstream tasks by default.
            enable_tracing: If True, creates OpenTelemetry spans for each task (requires opentelemetry-api).
            use_uvloop: If True, uses uvloop for a faster event loop (requires uvloop installed).
            tracer_provider: Optional OpenTelemetry tracer provider; if None, uses global provider.
            otlp_endpoint: OTLP gRPC endpoint (e.g., "http://localhost:4317"). If set, configures OTLP exporter.
            otlp_headers: Optional headers for OTLP exporter (e.g., authorization).
            otlp_insecure: If True, disables TLS for OTLP exporter (useful for local dev).
            enable_metrics: If True, enables Prometheus metrics collection (requires prometheus-client).
            metrics_port: Optional port number to start an HTTP server exposing /metrics. If None, metrics are only available programmatically.
        """
        if use_uvloop:
            _maybe_use_uvloop()
        self.tasks: Dict[str, Task] = {}  # name -> Task
        self.dag = DAG()
        self.start_time = 0
        self.plugin_mgr = PluginManager()
        self.resource_limits = resource_limits or {}
        self.enable_cancellation = enable_cancellation_propagation
        self.enable_tracing = enable_tracing
        self._tracer = None
        self._otlp_exporter = None
        if enable_tracing:
            try:
                from opentelemetry import trace
                from opentelemetry.sdk.trace import TracerProvider
                from opentelemetry.sdk.trace.export import BatchSpanProcessor
                # If tracer_provider is provided, use it directly
                if tracer_provider:
                    self._tracer = trace.get_tracer(__name__, tracer_provider=tracer_provider)
                else:
                    # Set up a default TracerProvider with optional OTLP exporter
                    provider = TracerProvider()
                    if otlp_endpoint:
                        try:
                            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                            self._otlp_exporter = OTLPSpanExporter(
                                endpoint=otlp_endpoint,
                                headers=otlp_headers or {},
                                insecure=otlp_insecure
                            )
                            processor = BatchSpanProcessor(self._otlp_exporter)
                            provider.add_span_processor(processor)
                        except ImportError:
                            # OTLP exporter not available; continue without export
                            pass
                    # Set global provider
                    trace.set_tracer_provider(provider)
                    self._tracer = trace.get_tracer(__name__)
                self.enable_tracing = True
            except ImportError:
                self.enable_tracing = False  # degrade gracefully

        # Profiling integration (py-spy)
        self.enable_profiling = enable_profiling
        self.profile_output = profile_output or f"profile-{int(time.time())}.json"
        self._profile_proc = None

        # Metrics integration (optional)
        self.enable_metrics = enable_metrics
        self.metrics_port = metrics_port
        self._metrics_registry = None
        self._task_counter = None
        self._task_duration = None
        self._dag_size_gauge = None
        self._active_tasks_gauge = None
        self._resource_usage_gauges = {}
        self._metrics_server_thread = None
        if self.enable_metrics:
            try:
                from prometheus_client import Counter, Histogram, Gauge, start_http_server, REGISTRY
                self._metrics_registry = REGISTRY
                self._task_counter = Counter('catalyst_tasks_total', 'Total tasks executed', ['name', 'status'], registry=self._metrics_registry)
                self._task_duration = Histogram('catalyst_task_duration_seconds', 'Task execution duration', ['name'], registry=self._metrics_registry)
                self._dag_size_gauge = Gauge('catalyst_dag_size', 'Number of tasks in DAG', registry=self._metrics_registry)
                self._active_tasks_gauge = Gauge('catalyst_active_tasks', 'Number of currently executing tasks', registry=self._metrics_registry)
                # Resource usage gauges will be created lazily per resource
                if self.metrics_port is not None:
                    start_http_server(self.metrics_port, registry=self._metrics_registry)
            except ImportError:
                warnings.warn("prometheus-client not installed; metrics collection disabled", RuntimeWarning)
                self.enable_metrics = False

        self._resource_semaphores: Dict[str, asyncio.BoundedSemaphore] = {}
        self._cancellation_flags: Dict[str, bool] = {}  # task name -> cancelled?
        # Initialize plugin manager with caching for performance
        self.plugin_mgr = PluginManager(cache_size=128)

        # Initialize semaphores for each resource type based on limits
        for resource, limit in self.resource_limits.items():
            # Convert float limits to integer semaphore counts (1 unit = 1 permit)
            # For fractional resources, we scale up (e.g., 0.5 cpu = 1 permit with half usage tracking)
            # Simplified: treat each resource unit as one permit
            self._resource_semaphores[resource] = asyncio.BoundedSemaphore(int(limit))

    def load_plugins(self, plugin_dir: str = "plugins/builtin") -> None:
        """
        Dynamically load built-in plugins from a directory.

        Each .py file in plugin_dir should define either a Plugin subclass
        or provide a run/execute function. They are wrapped automatically.

        If a corresponding .yaml manifest exists with the same base name,
        the plugin will be instantiated using the manifest's configuration
        defaults (unused options are ignored by the plugin constructor).
        """
        if not os.path.exists(plugin_dir):
            return

        for item in os.listdir(plugin_dir):
            if item.endswith(".py") and item != "__init__.py":
                module_name = f"plugins.builtin.{item[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    # Find a Plugin subclass in the module, if any
                    plugin_cls = None
                    for _, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, Plugin) and obj is not Plugin:
                            plugin_cls = obj
                            break
                    if plugin_cls:
                        # Look for a manifest file next to the module
                        base = item[:-3]
                        manifest_path = os.path.join(plugin_dir, f"{base}.yaml")
                        if os.path.exists(manifest_path):
                            # Load plugin using manifest for config defaults and metadata
                            # auto_install defaults to False; dependencies must be installed beforehand
                            self.plugin_mgr.load_manifest(manifest_path, plugin_cls, auto_install=False)
                        else:
                            # No manifest; instantiate plugin with no config (use class defaults)
                            self.plugin_mgr.load_from_module(module, plugin_class=plugin_cls)
                    else:
                        # No explicit Plugin subclass; fall back to module adapter (run/execute)
                        self.plugin_mgr.load_from_module(module)
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")

    def add_task(
        self,
        name: str,
        func: Callable = None,
        depends_on: Optional[List[str]] = None,
        plugin: Optional[str] = None,
        resources: Optional[Dict[str, float]] = None,
        timeout: Optional[float] = None,
        retry_policy: Optional[Dict] = None,
        *args,
        **kwargs
    ) -> str:
        """
        Add a task to the orchestrator.

        Args:
            name: Unique task name
            func: Python callable (if not using plugin)
            depends_on: List of task names that must complete before this task
            plugin: Plugin name to use instead of a Python function
            resources: Resource requirements (e.g., {"cpu": 1.0, "memory_mb": 512})
            timeout: Timeout in seconds (None = no timeout)
            retry_policy: Retry config ({"max_attempts": N, "backoff_factor": X})
            *args, **kwargs: Arguments passed to the task function/plugin

        Returns:
            Task ID (short string)
        """
        if name in self.tasks:
            raise ValueError(f"Task '{name}' already exists")

        task = Task(
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            depends_on=depends_on or [],
            plugin_name=plugin
        )
        self.tasks[name] = task

        # Register with DAG, including Phase 2 enhancements
        try:
            self.dag.add_task(
                name,
                dependencies=set(depends_on or []),
                resources=resources,
                timeout=timeout,
                retry_policy=retry_policy,
                **kwargs  # pass through any extra metadata
            )
        except ValueError as e:
            raise

        # Update DAG size gauge if metrics enabled
        if self.enable_metrics and self._dag_size_gauge is not None:
            self._dag_size_gauge.set(len(self.dag))

        return task.id

    async def _run_task(self, task: Task) -> None:
        """Execute a single task with resource acquisition, timeout, retry, and cancellation."""
        # Check if this task has been cancelled due to upstream failure
        if self.enable_cancellation and self._cancellation_flags.get(task.name, False):
            task.status = TaskStatus.FAILED
            task.result = RuntimeError("Task cancelled due to upstream failure")
            return

        start_time = time.perf_counter()
        dag_node = self.dag.get_task(task.name)
        retry_policy = dag_node.retry_policy
        max_attempts = retry_policy.get("max_attempts", 1)
        backoff_factor = retry_policy.get("backoff_factor", 1.0)
        attempt = 0
        last_exception = None

        if self.enable_metrics and self._active_tasks_gauge is not None:
            self._active_tasks_gauge.inc()
        try:
            while attempt < max_attempts:
                attempt += 1
                try:
                    # Acquire resource semaphores (if resource tracking enabled)
                    semaphore_acquired = []
                    if self.resource_limits:
                        for resource, requirement in dag_node.resources.items():
                            if resource not in self._resource_semaphores:
                                continue  # No limit for this resource type
                            # Simplified: acquire one semaphore per unit (floor of requirement)
                            permits = max(1, int(requirement))
                            for _ in range(permits):
                                await self._resource_semaphores[resource].acquire()
                                semaphore_acquired.append(resource)

                    # Set up timeout if specified
                    task_coro = self._execute_task_internal(task)
                    if dag_node.timeout:
                        task_future = asyncio.wait_for(task_coro, timeout=dag_node.timeout)
                    else:
                        task_future = task_coro

                    # Execute the task (with tracing if enabled)
                    if self.enable_tracing:
                        result = await task_future
                    else:
                        result = await task_future

                    # Release resources
                    for resource in semaphore_acquired:
                        self._resource_semaphores[resource].release()

                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.duration = time.perf_counter() - start_time
                    # Record metrics for successful completion
                    if self.enable_metrics:
                        if self._task_counter:
                            self._task_counter.labels(name=task.name, status='completed').inc()
                        if self._task_duration:
                            self._task_duration.labels(name=task.name).observe(task.duration)
                    # Success - exit retry loop
                    return

                except asyncio.TimeoutError as e:
                    last_exception = e
                    task.result = e
                    # Release any acquired resources
                    for resource in semaphore_acquired:
                        self._resource_semaphores[resource].release()
                    # Backoff before retry
                    if attempt < max_attempts:
                        await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
                    continue

                except Exception as e:
                    last_exception = e
                    task.result = e
                    # Release any acquired resources
                    for resource in semaphore_acquired:
                        self._resource_semaphores[resource].release()
                    # Check if this exception should trigger retry
                    retry_on = retry_policy.get("retry_on", [])
                    if retry_on and not any(isinstance(e, rt) for rt in retry_on):
                        # Not a retryable exception
                        break
                    # Backoff before retry
                    if attempt < max_attempts:
                        await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
                    continue

            # All attempts exhausted or non-retryable error
            task.status = TaskStatus.FAILED
            task.duration = time.perf_counter() - start_time
            # Record metrics for failure
            if self.enable_metrics and self._task_counter:
                self._task_counter.labels(name=task.name, status='failed').inc()
            # If cancellation propagation is enabled, mark downstream tasks as cancelled
            if self.enable_cancellation and last_exception is not None:
                self._propagate_cancellation(task.name)
        finally:
            if self.enable_metrics and self._active_tasks_gauge is not None:
                self._active_tasks_gauge.dec()

    async def run(self) -> float:
        """
        Run all tasks respecting dependencies, resource limits, and retry policies.

        Returns:
            Total duration in seconds.
        """
        # Validate the DAG before execution
        try:
            layers = self.dag.topological_sort()
        except DAGError as e:
            raise RuntimeError(f"DAG validation failed: {e}")

        # Reset cancellation flags from any previous runs
        self._cancellation_flags.clear()

        self.start_time = time.perf_counter()

        # Profiling: start py-spy if enabled
        profiling_proc = None
        if self.enable_profiling:
            try:
                profiling_proc = self._start_profiling()
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to start profiling: {e}. Continuing without profiling.")

        # Tracing: create top-level span for this orchestration run
        span_ctx = None
        if self.enable_tracing and self._tracer:
            span_ctx = self._tracer.start_as_current_span(
                "orchestrator.run",
                attributes={
                    "orchestrator.tasks_count": len(self.tasks),
                    "orchestrator.layers_count": len(layers),
                }
            )
            span_ctx.__enter__()

        try:
            # Execute tasks layer by layer in parallel using structured concurrency.
            # Resource semaphores within tasks enforce limits.
            task_map = self.tasks  # name -> Task

            for layer_idx, layer in enumerate(layers):
                # Filter out cancelled tasks
                active_layer = [task_map[name] for name in layer if not self._cancellation_flags.get(name, False)]
                if not active_layer:
                    continue

                # Run all tasks in this layer concurrently with TaskGroup for better cancellation
                async with asyncio.TaskGroup() as tg:
                    for task in active_layer:
                        tg.create_task(self._run_task(task))

            total_duration = time.perf_counter() - self.start_time
            return total_duration
        finally:
            if span_ctx is not None:
                span_ctx.__exit__(None, None, None)
            if profiling_proc is not None:
                try:
                    profiling_proc.terminate()
                    profiling_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    profiling_proc.kill()

    async def _execute_task_internal(self, task: Task) -> Any:
        """Internal task execution without retry/timeout wrapping."""
        try:
            # Tracing: create span for this task execution
            span_ctx = None
            if self.enable_tracing and self._tracer:
                span_ctx = self._tracer.start_as_current_span(
                    f"task.execute.{task.name}",
                    attributes={
                        "task.name": task.name,
                        "task.plugin": task.plugin_name or "function",
                        "task.dependencies": ",".join(task.depends_on) if task.depends_on else "",
                    }
                )
                span_ctx.__enter__()
            else:
                span_ctx = None

            if task.plugin_name:
                plugin = self.plugin_mgr.get(task.plugin_name)
                if plugin is None:
                    raise ValueError(f"Plugin '{task.plugin_name}' not found")
                result = await plugin.execute(*task.args, **task.kwargs)
                return result
            elif task.func:
                # Call the function
                result = task.func(*task.args, **task.kwargs)
                # If the result is a coroutine (e.g., from a lambda returning an async call),
                # await it to support flexible callable patterns
                if inspect.iscoroutine(result):
                    result = await result
                return result
            else:
                raise ValueError(f"Task '{task.name}' has no function or plugin")

        except Exception as e:
            # Let the retry wrapper handle the exception
            raise
        finally:
            if span_ctx is not None:
                span_ctx.__exit__(None, None, None)

    def _propagate_cancellation(self, failed_task_name: str) -> None:
        """
        Mark all downstream tasks (dependents) as cancelled due to upstream failure.
        Recursively cancels the entire downstream subgraph.
        """
        dag_node = self.dag.get_task(failed_task_name)
        to_cancel = list(dag_node.dependents)

        while to_cancel:
            current = to_cancel.pop()
            if current in self._cancellation_flags:
                continue  # Already cancelled
            self._cancellation_flags[current] = True
            # Immediately mark the task as FAILED (if still pending)
            task = self.tasks.get(current)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.FAILED
                task.result = RuntimeError(f"Cancelled due to failure of {failed_task_name}")
            # Add its dependents to the queue
            downstream_node = self.dag.get_task(current)
            to_cancel.extend(downstream_node.dependents)

    def _start_profiling(self) -> subprocess.Popen:
        """
        Start py-spy as a subprocess to profile the current Python process.

        Returns:
            subprocess.Popen instance for the profiling process.
        """
        # Determine py-spy command: try 'py-spy' then 'python -m py_spy'
        try:
            subprocess.run(["py-spy", "--version"], capture_output=True, check=True, timeout=1)
            cmd = ["py-spy", "record", "-o", self.profile_output, "--pid", str(os.getpid())]
        except Exception:
            # Try module invocation
            cmd = [sys.executable, "-m", "py_spy", "record", "-o", self.profile_output, "--pid", str(os.getpid())]
        # Start the subprocess; capture output to avoid cluttering console
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc

    def report(self) -> None:
        """Print a summary of task execution results."""
        print(f"\n[Catalyst] Orchestration Complete")
        print("-" * 40)
        for t in self.tasks.values():
            # Use plain ASCII status markers for cross-platform compatibility
            status_icon = "[OK]" if t.status == TaskStatus.COMPLETED else "[ERR]"
            print(f"{status_icon} Task: {t.name:<20} | Status: {t.status.value:<10} | Time: {t.duration:.4f}s")
        print("-" * 40)

    # Additional utility methods

    def get_dag(self) -> DAG:
        """Return the underlying DAG for introspection."""
        return self.dag

    @property
    def resource_pool(self) -> Dict[str, asyncio.BoundedSemaphore]:
        """Return the dictionary of resource semaphores for introspection."""
        return self._resource_semaphores

    def validate(self) -> None:
        """Validate DAG structure without running."""
        self.dag.validate()

    async def clear(self) -> None:
        """Clear all tasks and DAG state."""
        self.tasks.clear()
        self.dag = DAG()
        if self.enable_metrics and self._dag_size_gauge is not None:
            self._dag_size_gauge.set(0)
        await self.plugin_mgr.clear()
        self._cancellation_flags.clear()
        # Reinitialize resource semaphores
        self._resource_semaphores.clear()
        for resource, limit in self.resource_limits.items():
            self._resource_semaphores[resource] = asyncio.BoundedSemaphore(int(limit))

    def load_yaml(self, path: str) -> None:
        """
        Load a workflow definition from a YAML file and register tasks.

        Args:
            path: Path to a YAML workflow file.

        The YAML format supports the following task keys:
          - name (required)
          - plugin: plugin name to use
          - func: Python callable reference (e.g., 'module:func' or 'module.submodule.func')
          - depends_on: list of task names
          - resources: dict of resource requirements (cpu, memory_mb, etc.)
          - timeout: float seconds
          - retry_policy: dict (max_attempts, backoff_factor, retry_on)
          - args: list of positional arguments
          - kwargs: dict of keyword arguments
          Any additional keys are passed as kwargs to the task.
        """
        try:
            import yaml
        except ImportError as e:
            raise ImportError(
                "PyYAML is required for YAML loading. Install with 'pip install pyyaml'"
            ) from e

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("YAML root must be a mapping")
        tasks_data = data.get('tasks', [])
        if not isinstance(tasks_data, list):
            raise ValueError("'tasks' section must be a list")

        for task_def in tasks_data:
            if not isinstance(task_def, dict):
                raise ValueError("Each task entry must be a mapping")
            name = task_def.pop('name', None)
            if not name:
                raise ValueError("Task missing required 'name' field")

            plugin = task_def.pop('plugin', None)
            func = task_def.pop('func', None)
            depends_on = task_def.pop('depends_on', []) or []
            resources = task_def.pop('resources', None)
            timeout = task_def.pop('timeout', None)
            retry_policy = task_def.pop('retry_policy', None)
            args = task_def.pop('args', [])
            kwargs = task_def.pop('kwargs', {})

            # Resolve function string references to callables
            if func and isinstance(func, str):
                func = self._resolve_function_ref(func)

            # Merge any remaining keys into kwargs (for plugin-specific config)
            kwargs = {**kwargs, **task_def}

            self.add_task(
                name,
                func=func,
                depends_on=depends_on,
                plugin=plugin,
                resources=resources,
                timeout=timeout,
                retry_policy=retry_policy,
                *args,
                **kwargs
            )

    def _resolve_function_ref(self, ref: str) -> Callable:
        """
        Resolve a string reference like 'module:func' or 'module.submodule.func' to a callable.
        """
        if ':' in ref:
            module_name, attr = ref.split(':', 1)
        elif '.' in ref:
            parts = ref.rsplit('.', 1)
            if len(parts) == 2:
                module_name, attr = parts
            else:
                module_name = ref
                attr = None
        else:
            module_name = ref
            attr = None

        try:
            module = importlib.import_module(module_name)
            if attr:
                obj = getattr(module, attr)
            else:
                obj = module
            return obj
        except Exception as e:
            raise ImportError(f"Could not import '{ref}': {e}") from e
