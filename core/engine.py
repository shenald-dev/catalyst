"""
Catalyst Core: High-performance task orchestration.
"""
import asyncio
import time
import uuid
import importlib
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Any, Type
from core.resolver import DAGResolver

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
    def __init__(self):
        self.tasks: List[Task] = []
        self.start_time = 0
        self.resolver = DAGResolver()
        self.plugins: Dict[str, Any] = {}

    def load_plugins(self, plugin_dir="plugins/builtin"):
        """Dynamically loads built-in plugins."""
        if not os.path.exists(plugin_dir):
            return
        
        for item in os.listdir(plugin_dir):
            if item.endswith(".py") and item != "__init__.py":
                module_name = f"plugins.builtin.{item[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    # Simple registration: look for a class that inherits from a base or just register the module
                    self.plugins[item[:-3]] = module
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")

    def add_task(self, name: str, func: Callable = None, depends_on: List[str] = None, plugin: str = None, *args, **kwargs):
        task = Task(name=name, func=func, args=args, kwargs=kwargs, depends_on=depends_on or [], plugin_name=plugin)
        self.tasks.append(task)
        return task.id

    async def _run_task(self, task: Task):
        task.status = TaskStatus.RUNNING
        start = time.perf_counter()
        try:
            if task.plugin_name and task.plugin_name in self.plugins:
                # If it's a plugin task, use the plugin's 'run' or 'execute' function
                plugin_mod = self.plugins[task.plugin_name]
                if hasattr(plugin_mod, "run"):
                    task.result = await plugin_mod.run(*task.args, **task.kwargs)
                else:
                    task.result = plugin_mod.execute(*task.args, **task.kwargs)
            elif task.func:
                if asyncio.iscoroutinefunction(task.func):
                    task.result = await task.func(*task.args, **task.kwargs)
                else:
                    task.result = task.func(*task.args, **task.kwargs)
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.result = e
            task.status = TaskStatus.FAILED
        task.duration = time.perf_counter() - start

    async def run_sequential_layers(self):
        self.start_time = time.perf_counter()
        
        task_data = [{"name": t.name, "depends_on": t.depends_on} for t in self.tasks]
        layers = self.resolver.resolve(task_data)
        
        task_map = {t.name: t for t in self.tasks}
        
        for layer in layers:
            await asyncio.gather(*(self._run_task(task_map[name]) for name in layer))
            
        total_duration = time.perf_counter() - self.start_time
        return total_duration

    def report(self):
        print(f"\n🚀 [Catalyst] Orchestration Complete")
        print("-" * 40)
        for t in self.tasks:
            status_color = "✅" if t.status == TaskStatus.COMPLETED else "❌"
            print(f"{status_color} Task: {t.name:<15} | Status: {t.status.value:<10} | Time: {t.duration:.4f}s")
        print("-" * 40)
