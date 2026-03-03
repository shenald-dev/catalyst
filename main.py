"""
Catalyst: The high-performance builder's engine.
"""
import asyncio
from core.engine import Orchestrator

async def main():
    engine = Orchestrator()
    
    # Load dynamic plugins
    engine.load_plugins()
    
    # Define complex workflow using both custom functions and plugins
    engine.add_task("pre_flight", plugin="shell", command="echo 'Initializing Catalyst Engine...'")
    engine.add_task("list_files", plugin="shell", command="dir /b", depends_on=["pre_flight"])
    
    print("✨ [Catalyst] Initializing hybrid plugin-aware workflow...")
    duration = await engine.run_sequential_layers()
    
    engine.report()
    
    # Showcase plugin results
    for t in engine.tasks:
        if t.plugin_name:
            print(f"[{t.name}] Result: {t.result}")

    print(f"\nTotal Workflow Time: {duration:.4f}s")

if __name__ == "__main__":
    asyncio.run(main())
