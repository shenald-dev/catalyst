"""
Catalyst: The high-performance builder's engine.
"""
import asyncio
from core.engine import Orchestrator

async def task_a():
    print("[A] Building project core...")
    await asyncio.sleep(1)
    return "Core Ready"

async def task_b():
    print("[B] Running internal diagnostics...")
    await asyncio.sleep(0.5)
    return "Diagnostics Pass"

async def task_c():
    print("[C] Finalizing deployment...")
    await asyncio.sleep(1)
    return "Deployed"

async def main():
    engine = Orchestrator()
    
    # Define complex workflow
    engine.add_task("build_core", task_a)
    engine.add_task("run_tests", task_b, depends_on=["build_core"])
    engine.add_task("deploy_app", task_c, depends_on=["run_tests"])
    
    print("✨ [Catalyst] Initializing dependency-aware workflow...")
    duration = await engine.run_sequential_layers()
    
    engine.report()
    print(f"Total Workflow Time: {duration:.4f}s")

if __name__ == "__main__":
    asyncio.run(main())
