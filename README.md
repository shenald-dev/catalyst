# Catalyst

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/catalyst.svg)](https://badge.fury.io/py/catalyst)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/shenald-dev/catalyst/workflows/Test/badge.svg)](https://github.com/shenald-dev/catalyst/actions)
[![Coverage](https://img.shields.io/badge/coverage-100%25-green.svg)](https://github.com/shenald-dev/catalyst)

🚀 **High-performance workflow orchestration for the modern builder.**

Catalyst is an intentional, high-performance task engine designed to handle complex workflows with ease. It leverages asynchronous execution and parallel processing to ensure your build pipelines are as fast as possible.

## ✨ Philosophy

Build with speed, build with intent. Catalyst is the result of deep-diving into systems design to create a tool that handles the "heavy lifting" of workflow automation without the boilerplate.

## 🛠️ Features (v0.3.0 - Phase 3)

- **Parallel Execution:** Native asyncio concurrency with layer-based execution.
- **DAG-Based Orchestration:** Automatic topological sorting, cycle detection, critical path, makespan estimation, DOT export.
- **Graph Introspection:** Query ancestors, descendants, depth, and reachability for any task (enables monitoring and dynamic decisions).
- **Resource-Aware Scheduling:** Limit CPU, memory, or custom resources with semaphore-based gating.
- **Robust Error Handling:** Per-task timeouts, configurable retry policies (exponential backoff, exception filters).
- **Cancellation Propagation:** Optional fail-fast for downstream tasks when upstream fails.
- **Declarative Workflows:** Load entire pipelines from YAML files with `Orchestrator.load_yaml()`.
- **Observability:** Optional OpenTelemetry tracing with configurable OTLP exporter for sending spans to observability backends.
- **Metrics Export:** Optional Prometheus metrics endpoint (`/metrics`) exposing task counts, durations, DAG size, and active tasks.
- **High-Performance Serialization:** msgspec-accelerated DAG serialization (fallback to JSON).
- **Profiling Integration:** On-demand py-spy profiling to identify hot paths and performance bottlenecks (`enable_profiling=True`).
- **Configuration Management:** Flexible overrides via YAML files, environment variables (`CATALYST_*`), and runtime parameters.
- **Structured Logging:** Optional JSON log output for production observability (uses `structlog` if available, otherwise custom formatter).
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

## ⚙️ Configuration

Catalyst supports flexible configuration via multiple sources (lowest precedence first):

1. **Defaults** built into the code.
2. **YAML configuration file** (`~/.catalyst/config.yaml` or path set by `CATALYST_CONFIG`).
3. **Environment variables** with prefix `CATALYST_` (e.g., `CATALYST_ENABLE_METRICS=true`).
4. **Runtime arguments** passed to `Orchestrator.__init__()`.

Available configuration keys:

| Key                     | Type    | Default | Description |
|-------------------------|---------|---------|-------------|
| `resource_limits`       | dict    | `{}`    | Resource limits (e.g., `{"cpu": 4.0, "memory_mb": 8192}`) |
| `enable_cancellation`   | bool    | `True`  | Cancel downstream tasks on upstream failure |
| `enable_tracing`        | bool    | `False` | Enable OpenTelemetry tracing |
| `otlp_endpoint`         | str     | `None`  | OTLP gRPC endpoint for traces |
| `otlp_headers`          | dict    | `{}`    | Headers for OTLP exporter |
| `otlp_insecure`         | bool    | `False` | Disable TLS for OTLP (dev only) |
| `enable_metrics`        | bool    | `False` | Enable Prometheus metrics collection |
| `metrics_port`          | int     | `None`  | Port to expose `/metrics` HTTP endpoint |
| `enable_profiling`      | bool    | `False` | Enable py-spy profiling |
| `profile_output`        | str     | `None`  | Output file for profiling data (default: `profile-<timestamp>.json`) |
| `enable_json_logging`   | bool    | `False` | Enable structured JSON logging |
| `plugin_dirs`           | list    | `["plugins/builtin"]` | Directories to search for plugins |

**Example YAML config (`~/.catalyst/config.yaml`):**

```yaml
enable_metrics: true
metrics_port: 9090
resource_limits:
  cpu: 4.0
  memory_mb: 8192
enable_json_logging: true
```

**Example environment variables:**

```bash
export CATALYST_ENABLE_METRICS=true
export CATALYST_METRICS_PORT=9090
export CATALYST_ENABLE_JSON_LOGGING=true
```

Structured logging (when enabled) emits JSON lines with fields: `timestamp`, `level`, `logger`, `message`, and any extra context. It automatically uses `structlog` if installed; otherwise falls back to standard logging with a custom JSON formatter.

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/shenald-dev/catalyst.git
cd catalyst

# Install dependencies (PyYAML for YAML support)
pip install -r requirements.txt

# Or install directly (minimal core, no deps required)
# python -m pip install --upgrade catalyst  # (coming soon to PyPI)
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
