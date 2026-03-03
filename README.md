# Catalyst

> A workflow engine built because I got tired of waiting on slow CI pipelines.

Catalyst is a high-performance workflow orchestration engine for developers who value speed and simplicity. It handles complex DAG-based task scheduling with sub-second startup and minimal memory footprint.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build](https://github.com/shenald-dev/catalyst/actions/workflows/ci.yml/badge.svg)](https://github.com/shenald-dev/catalyst/actions)
[![codecov](https://codecov.io/gh/shenald-dev/catalyst/branch/main/graph/badge.svg)](https://codecov.io/gh/shenald-dev/catalyst)
[![PyPI version](https://badge.fury.io/py/catalyst-py.svg)](https://badge.fury.io/py/catalyst-py)

## Why Catalyst?

After maintaining a monorepo with 500+ packages, I found existing schedulers either too slow or overly complex. I wanted something that *just works* — fast, predictable, and easy to debug.

So I built Catalyst from scratch, focusing on core principles: speed, simplicity, and developer experience.

## Features

- **DAG-based scheduling** — Topological sorting with cycle detection
- **Parallel execution** — Run up to 100 concurrent tasks efficiently
- **Resource-aware** — Semaphore-based resource limiting
- **Critical path analysis** — Identify bottlenecks
- **YAML definitions** — Declarative workflow configuration
- **Zero-bloat** — Pure Python stdlib (PyYAML optional)
- **Observability** — Optional OpenTelemetry integration

## Performance

- 1000-node DAG sort: <1s
- 100 parallel tasks: <0.2s
- Memory overhead: ~12MB

## Quick Start

\`\`\`bash
pip install catalyst-py
\`\`\`

\`\`\`python
from catalyst import Orchestrator

engine = Orchestrator()
engine.load_plugins()

engine.add_task("build", plugin="shell", command="npm run build")
engine.add_task("test", plugin="shell", command="npm test", depends_on=["build"])

await engine.run()
engine.report()
\`\`\`

## Documentation

- [Installation](docs/installation.md)
- [CLI Reference](docs/cli.md)
- [Workflow Syntax](docs/workflow.md)
- [API Guide](docs/api.md)
- [Performance Benchmarks](benchmarks/README.md)

## License

MIT © [Shenald](https://github.com/shenald-dev)

---

*Built with intention. Shipped with speed.*
