"""
Catalyst Core: High-performance task orchestration.
"""
import asyncio
import inspect
import time
import uuid
import importlib
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Any, Optional
from core.dag import DAG, DAGError
from core.plugin import PluginManager


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
    """
    def __init__(self):
        self.tasks: Dict[str, Task] = {}  # name -> Task
        self.dag = DAG()
        self.start_time = 0
        self.plugin_mgr = PluginManager()

    def load_plugins(self, plugin_dir: str = "plugins/builtin") -> None:
        """
        Dynamically load built-in plugins from a directory.

        Each .py file in plugin_dir should define either a Plugin subclass
        or provide a run/execute function. They are wrapped automatically.
        """
        if not os.path.exists(plugin_dir):
            return

        for item in os.listdir(plugin_dir):
            if item.endswith(".py") and item != "__init__.py":
                module_name = f"plugins.builtin.{item[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    self.plugin_mgr.load_from_module(module)
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")

    def add_task(
        self,
        name: str,
        func: Callable = None,
        depends_on: Optional[List[str]] = None,
        plugin: Optional[str] = None,
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

        # Register with DAG (dependencies will be validated later)
        try:
            self.dag.add_task(name, dependencies=set(depends_on or []))
        except ValueError as e:
            raise

        return task.id

    async def _run_task(self, task: Task) -> None:
        """Execute a single task (with plugin or function)."""
        task.status = TaskStatus.RUNNING
        start = time.perf_counter()
        try:
            if task.plugin_name:
                plugin = self.plugin_mgr.get(task.plugin_name)
                if plugin is None:
                    raise ValueError(f"Plugin '{task.plugin_name}' not found")
                task.result = await plugin.execute(*task.args, **task.kwargs)
            elif task.func:
                if inspect.iscoroutinefunction(task.func):
                    task.result = await task.func(*task.args, **task.kwargs)
                else:
                    task.result = task.func(*task.args, **task.kwargs)
            else:
                raise ValueError(f"Task '{task.name}' has no function or plugin")
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.result = e
            task.status = TaskStatus.FAILED
        task.duration = time.perf_counter() - start

    async def run(self) -> float:
        """
        Run all tasks respecting dependencies.

        Returns:
            Total duration in seconds.
        """
        # Validate the DAG before execution
        try:
            layers = self.dag.topological_sort()
        except DAGError as e:
            raise RuntimeError(f"DAG validation failed: {e}")

        self.start_time = time.perf_counter()

        # Execute tasks layer by layer in parallel
        task_map = self.tasks  # name -> Task

        for layer in layers:
            # Gather tasks for this layer
            layer_tasks = [task_map[name] for name in layer]
            # Run them concurrently
            await asyncio.gather(*(self._run_task(t) for t in layer_tasks))

        total_duration = time.perf_counter() - self.start_time
        return total_duration

    def report(self) -> None:
        """Print a summary of task execution results."""
        print(f"\n🚀 [Catalyst] Orchestration Complete")
        print("-" * 40)
        for t in self.tasks.values():
            status_icon = "✅" if t.status == TaskStatus.COMPLETED else "❌"
            print(f"{status_icon} Task: {t.name:<20} | Status: {t.status.value:<10} | Time: {t.duration:.4f}s")
        print("-" * 40)

    # Additional utility methods

    def get_dag(self) -> DAG:
        """Return the underlying DAG for introspection."""
        return self.dag

    def validate(self) -> None:
        """Validate DAG structure without running."""
        self.dag.validate()

    def clear(self) -> None:
        """Clear all tasks and DAG state."""
        self.tasks.clear()
        self.dag = DAG()
        self.plugin_mgr.clear()
