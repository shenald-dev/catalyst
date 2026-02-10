"""
Catalyst Core: High-performance task orchestration.
"""
import asyncio
import time
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Any

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    name: str
    func: Callable
    args: tuple = ()
    kwargs: Dict = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    duration: float = 0.0

from core.resolver import DAGResolver

class Orchestrator:
    def __init__(self):
        self.tasks: List[Task] = []
        self.start_time = 0
        self.resolver = DAGResolver()

    def add_task(self, name: str, func: Callable, depends_on: List[str] = None, *args, **kwargs):
        task = Task(name=name, func=func, args=args, kwargs=kwargs, depends_on=depends_on or [])
        self.tasks.append(task)
        return task.id

    async def run_sequential_layers(self):
        self.start_time = time.perf_counter()
        
        # Prepare task dict for resolver
        task_data = [{"name": t.name, "depends_on": t.depends_on} for t in self.tasks]
        layers = self.resolver.resolve(task_data)
        
        task_map = {t.name: t for t in self.tasks}
        
        for layer in layers:
            await asyncio.gather(*(self._run_task(task_map[name]) for name in layer))
            
        total_duration = time.perf_counter() - self.start_time
        return total_duration

    async def run_all(self):
        """Legacy run_all (parallel without dependencies)"""
        return await self.run_sequential_layers()

    def report(self):
        print(f"\n🚀 [Catalyst] Orchestration Complete")
        print("-" * 40)
        for t in self.tasks:
            status_color = "✅" if t.status == TaskStatus.COMPLETED else "❌"
            print(f"{status_color} Task: {t.name:<15} | Status: {t.status.value:<10} | Time: {t.duration:.4f}s")
        print("-" * 40)
