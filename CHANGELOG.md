# Changelog

All notable changes to Catalyst will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-03-06 (Unreleased)

### Added
- **Resource-aware makespan estimation:** `DAG.estimated_makespan(resource_limits={...})` simulates list scheduling to predict execution time under constrained resources.
- **Benchmark suite:** Microbenchmarks in `benchmarks/run_benchmarks.py` for topological sort, makespan, and critical path performance.
- **Graph query utilities:** `get_ancestors()`, `get_descendants()`, `get_depth()`, `is_reachable()` for advanced DAG introspection.

### Improved
- Makespan estimation API now supports both unlimited (critical path) and constrained scenarios.
- Test suite expanded (74 tests) with resource-aware makespan validation and edge cases.

## [0.3.0] - 2026-03-05

### Added
- **Phase 3 Complete** — Full plugin ecosystem with auto-discovery and manifest format
- Plugin manifest support (YAML) for metadata, dependencies, and config validation
- Automatic dependency resolution: `auto_install=True` triggers `pip install` for missing plugin dependencies
- LRU-cached plugin lookups for minimal overhead
- Built-in plugins: `shell`, upgraded `http` (aiohttp with connection pooling, retries, circuit breaker), `database`, `cache`, `notify`, `docker`
- OpenTelemetry tracing integration with configurable OTLP exporter
- Prometheus metrics endpoint (`/metrics`) exposing task counts, durations, DAG size, active tasks
- msgspec-accelerated DAG serialization (fallback to JSON)
- On-demand py-spy profiling (`enable_profiling=True`)
- Per-task timeout and retry with exponential backoff
- Cancellation propagation (fail-fast for downstream tasks)
- YAML workflow definitions with `Orchestrator.load_yaml()`
- Resource-aware scheduling with semaphore-based gating
- Graph introspection: ancestors, descendants, depth, reachability queries
- Critical path analysis and makespan estimation
- DOT export for DAG visualization
- Comprehensive unit test suite (33 tests, 100% coverage)

### Improved
- Performance: 1000-node DAG topological sort <1s, 100 parallel tasks <0.2s
- Memory footprint reduced with msgspec and LRU caches
- Cross-platform compatibility (Windows console encoding fixed)
- Error handling: detailed errorRate metric, structured logging

### Fixed
- Initialization race conditions
- Windows service detection quirk (now uses direct socket test)

## [0.2.0] - 2025-02-15

### Added
- DAG-based task orchestration with topological sorting
- Iterative cycle detection using DFS
- Parallel execution with asyncio.TaskGroup
- Basic plugins: shell, http (requests-based), file, notify
- Simple YAML workflow support
- Basic retry logic

### Changed
- Switched from serial to async execution model
- Introduced resource limits (CPU, memory semaphores)

## [0.1.0] - 2025-01-10

### Added
- Initial prototype
- Task definition and execution
- Basic dependency resolution
- Simple command-line interface
