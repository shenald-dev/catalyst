# Catalyst

🚀 **High-performance workflow orchestration for the modern builder.**

Catalyst is an intentional, high-performance task engine designed to handle complex workflows with ease. It leverages asynchronous execution and parallel processing to ensure your build pipelines are as fast as possible.

## ✨ Philosophy

Build with speed, build with intent. Catalyst is the result of deep-diving into systems design to create a tool that handles the "heavy lifting" of workflow automation without the boilerplate.

## 🛠️ Features (v0.5 - Phase 4)

- **Parallel Execution:** Native asyncio concurrency with layer-based execution.
- **DAG-Based Orchestration:** Automatic topological sorting, cycle detection, critical path, makespan estimation, DOT export.
- **Graph Introspection:** Query ancestors, descendants, depth, and reachability for any task (enables monitoring and dynamic decisions).
- **Resource-Aware Scheduling:** Limit CPU, memory, or custom resources with semaphore-based gating.
- **Robust Error Handling:** Per-task timeouts, configurable retry policies (exponential backoff, exception filters).
- **Cancellation Propagation:** Optional fail-fast for downstream tasks when upstream fails.
- **Declarative Workflows:** Load entire pipelines from YAML files with `Orchestrator.load_yaml()`.
- **Observability:** Optional OpenTelemetry tracing with configurable OTLP exporter for sending spans to observability backends.
- **High-Performance Serialization:** msgspec-accelerated DAG serialization (fallback to JSON).
- **Profiling Integration:** On-demand py-spy profiling to identify hot paths and performance bottlenecks (`enable_profiling=True`).
- **Plugin Ecosystem:**
  - Auto-discovery of Plugin subclasses.
  - Plugin manifest format (YAML) for metadata, dependencies, and config validation via Pydantic.
  - Automatic dependency resolution: `auto_install=True` triggers `pip install` for missing plugin dependencies.
  - LRU-cached plugin lookups for minimal overhead.
  - Built-in plugins: `shell`, upgraded `http` (aiohttp with connection pooling, retries, circuit breaker), `database`, `cache`, `notify`, and new `docker` for container orchestration.
- **Minimalist Core:** No required external dependencies; optional PyYAML for YAML support.

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

### Plugin Manifests

For packaged plugins, provide a `plugin.yaml` alongside the module to declare metadata:

```yaml
plugin:
  name: "database"
  version: "0.2.0"
  description: "SQL execution with pooling"
  dependencies: ["aiosqlite", "asyncpg"]
config:
  defaults: { driver: "sqlite", database: ":memory:", pool_size: 5 }
```

The manifest enables dependency checks and config validation via Pydantic (if installed).  
**Note:** Built-in plugins already include manifest files, and their declared configuration defaults are automatically applied when `engine.load_plugins()` is called.

---

*Built with intention.*
