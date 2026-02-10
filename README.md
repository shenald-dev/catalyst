# Catalyst

🚀 **High-performance workflow orchestration for the modern builder.**

Catalyst is an intentional, high-performance task engine designed to handle complex workflows with ease. It leverages asynchronous execution and parallel processing to ensure your build pipelines are as fast as possible.

## ✨ Philosophy

Build with speed, build with intent. Catalyst is the result of deep-diving into systems design to create a tool that handles the "heavy lifting" of workflow automation without the boilerplate.

## 🛠️ Features (v0.2)

- **Parallel Execution:** Native support for `asyncio` and concurrent task handling.
- **Dependency Awareness:** Intelligent DAG resolution for complex task sequencing.
- **Dynamic Plugin System:** Extensible architecture allowing for custom task types (e.g., Shell, Git, Docker).
- **Minimalist Core:** Lightweight engine with zero external dependencies.

## 🚀 Quick Start

```python
from core.engine import Orchestrator

engine = Orchestrator()
engine.load_plugins()

engine.add_task("pre_flight", plugin="shell", command="echo 'Hello Catalyst'")
await engine.run_all()
```

---
*Built with intention.*
