"""
Catalyst: The high-performance builder's engine.
"""
import asyncio
import time
from core.engine import Orchestrator

async def mock_io_task(name, delay):
    await asyncio.sleep(delay)
    return f"{name} done"

def mock_cpu_task(name, n):
    res = sum(i * i for i in range(n))
    return res

async def main():
    engine = Orchestrator()
    
    # Adding tasks
    engine.add_task("io_intensive_1", mock_io_task, "Task A", 1.5)
    engine.add_task("io_intensive_2", mock_io_task, "Task B", 0.5)
    engine.add_task("cpu_intensive_1", mock_cpu_task, "Task C", 10**6)
    
    print("✨ [Catalyst] Initializing parallel workflow...")
    duration = await engine.run_all()
    
    engine.report()
    print(f"Total Workflow Time: {duration:.4f}s")

if __name__ == "__main__":
    asyncio.run(main())
