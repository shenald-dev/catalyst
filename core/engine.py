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
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    duration: float = 0.0

class Orchestrator:
    def __init__(self):
        self.tasks: List[Task] = []
        self.start_time = 0

    def add_task(self, name: str, func: Callable, *args, **kwargs):
        task = Task(name=name, func=func, args=args, kwargs=kwargs)
        self.tasks.append(task)
        return task.id

    async def _run_task(self, task: Task):
        task.status = TaskStatus.RUNNING
        start = time.perf_counter()
        try:
            if asyncio.iscoroutinefunction(task.func):
                task.result = await task.func(*task.args, **task.kwargs)
            else:
                task.result = task.func(*task.args, **task.kwargs)
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.result = e
            task.status = TaskStatus.FAILED
        task.duration = time.perf_counter() - start

    async def run_all(self):
        self.start_time = time.perf_counter()
        await asyncio.gather(*(self._run_task(t) for t in self.tasks))
        total_duration = time.perf_counter() - self.start_time
        return total_duration

    def report(self):
        print(f"\n🚀 [Catalyst] Orchestration Complete")
        print("-" * 40)
        for t in self.tasks:
            status_color = "✅" if t.status == TaskStatus.COMPLETED else "❌"
            print(f"{status_color} Task: {t.name:<15} | Status: {t.status.value:<10} | Time: {t.duration:.4f}s")
        print("-" * 40)
