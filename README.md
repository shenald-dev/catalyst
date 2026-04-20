# ✨ Catalyst Engine

> A high-performance workflow engine for complex pipelines. Parallel DAG execution. Zero bloat.

## Features
- **⚡ Parallel DAG Execution**: Blazing fast topology resolution with fail-fast optimization avoiding closure allocation overhead.
- **🏗️ Domain-Driven Design**: Clean, decoupled architecture.
- **🌐 FastAPI Dashboard**: Optional API and visualization endpoints.
- **🛡️ Strict Typing**: Fully typed with Python 3.10+ and `mypy`, leveraging built-in generic types.
- **💥 Graceful Failure Handling**: When an upstream task fails, it short-circuits execution gracefully, safely yielding a serializable JSON object (in the API representation) describing the exception instead of crashing the process.

## Architecture Highlights
The core logic lives in `src/catalyst/domain` and executes Directed Acyclic Graphs efficiently using purely native standard library features (such as `graphlib`). The `presentation` layer serves as a decoupled FastAPI interface.

## Quick Start
```bash
uv pip install -e .[dev]
uvicorn catalyst.presentation.api.main:app --reload
```

## 🤝 Contributing
Join the flow state and help us make Catalyst even faster! 🚀
- 🐛 **Found a bug?** Open an issue to let us know.
- ✨ **Have a feature idea?** We are open to PRs! Just make sure to run `ruff format` and keep the typed codebase pristine.
- 🎨 **Documentation tweaks?** Always welcome! 

*Built by a Vibe Coder. Focused on Performance.*
