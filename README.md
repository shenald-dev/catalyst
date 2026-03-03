# Catalyst

🚀 **High-performance workflow orchestration for the modern builder.**

Catalyst is an intentional, high-performance task engine designed to handle complex workflows with ease. It leverages asynchronous execution and parallel processing to ensure your build pipelines are as fast as possible.

## ✨ Philosophy

Build with speed, build with intent. Catalyst is the result of deep-diving into systems design to create a tool that handles the "heavy lifting" of workflow automation without the boilerplate.

## 🛠️ Features (v0.3 - Phase 2)

- **Parallel Execution:** Native asyncio concurrency with layer-based execution.
- **DAG-Based Orchestration:** Automatic topological sorting, cycle detection, and critical path analysis.
- **Resource-Aware Scheduling:** Limit CPU, memory, or custom resources with semaphore-based gating.
- **Robust Error Handling:** Per-task timeouts, configurable retry policies (exponential backoff, exception filters).
- **Cancellation Propagation:** Optional fail-fast for downstream tasks when upstream fails.
- **Declarative Workflows:** Load entire pipelines from YAML files with `Orchestrator.load_yaml()`.
- **Plugin Ecosystem:** Auto-discovery of Plugin subclasses; built-in plugins include `shell` and `http` (HTTP requests).
- **Minimalist Core:** No required external dependencies; optional PyYAML for YAML support.
- **Observability Ready:** Optional OpenTelemetry integration via `enable_tracing=True` (requires opentelemetry packages).

## 🚀 Quick Start

### Python API

```python
from core.engine import Orchestrator

engine = Orchestrator()
engine.load_plugins()

# Add tasks using plugins or Python functions
engine.add_task("pre_flight", plugin="shell", command="echo 'Initializing Catalyst Engine...'")
engine.add_task("api_call", plugin="http", method="GET", url="https://api.example.com/data")
engine.add_task("process", func=my_processing_function, depends_on=["api_call"])

await engine.run()
engine.report()
```

### YAML Definitions

Define your entire pipeline in a clean YAML file:

```yaml
# workflow.yaml
tasks:
  - name: pre_flight
    plugin: shell
    command: echo "Starting workflow"

  - name: fetch_data
    plugin: http
    method: GET
    url: https://api.example.com/data
    depends_on: [pre_flight]
    timeout: 10
    retry_policy:
      max_attempts: 3
      backoff_factor: 1.0

  - name: process
    func: mymodule.process_data
    depends_on: [fetch_data]
    resources:
      cpu: 1.0
```

Load and run:

```python
engine = Orchestrator(resource_limits={"cpu": 2.0})
engine.load_yaml("workflow.yaml")
await engine.run()
```

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/shenald-dev/catalyst.git
cd catalyst

# Optional: install PyYAML for YAML support
pip install -r requirements.txt

# Or just use the Python API directly (no dependencies required)
```

## 🧩 Writing Plugins

Plugins inherit from `core.plugin.Plugin` and implement `async def execute(self, **kwargs)`:

```python
from core.plugin import Plugin

class MyPlugin(Plugin):
    name = "myplugin"
    description = "Does something cool"

    async def execute(self, param1, param2):
        # your logic here
        return result
```

Place the plugin in `plugins/builtin/` and it will be auto-discovered when `engine.load_plugins()` is called.

---

*Built with intention.*
