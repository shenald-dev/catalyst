# ✨ Catalyst Engine

> A high-performance workflow engine for complex pipelines. Parallel DAG execution. Zero bloat.

## Features
- **⚡ Parallel DAG Execution**: Blazing fast topology resolution.
- **🏗️ Domain-Driven Design**: Clean, decoupled architecture.
- **🌐 FastAPI Dashboard**: Optional API and visualization endpoints.
- **🛡️ Strict Typing**: Fully typed with Python 3.10+ and `mypy`.

## Architecture Highlights
The core logic lives in `src/catalyst/domain` and executes Directed Acyclic Graphs efficiently using standard library features and `networkx`. The `presentation` layer serves as a decoupled FastAPI interface.

## Quick Start
```bash
uv pip install -e .[dev]
uvicorn catalyst.presentation.api.main:app --reload
```

*Built by a Vibe Coder. Focused on Performance.*
