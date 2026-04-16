# Changelog

All notable changes to this project will be documented in this file.

## [0.1.11] - 2026-04-09

### Verified
- Adversarial QA uncovered a subtle bug in `WorkflowEngine.add_task()` where `functools.partial` wrappers masked async functions as synchronous. Fixed by safely unwrapping `base_func` during task registration, passing all tests.
- Verified robust codebase typing by introducing `types-networkx` into local dev dependencies and dropping explicit `py.typed` marker files into `src/catalyst` and its subpackages.

### Changed
- Entropy Pruned: 0 lines (Maintained zero bloat).
- Dependencies Bumped: Deferred upgrading `pydantic-core` (strictly pinned at `2.41.5`) due to the known `SystemError` incompatibility during API tests.

## [0.1.10] - 2026-04-08

### Verified
- Adversarial QA confirmed the test suite is stable. Updated `pyproject.toml` test configuration to clear `pytest-asyncio` deprecation warnings.

### Changed
- Entropy Pruned: 0 lines (Maintained zero bloat).
- Dependencies Bumped: Deferred upgrading `pydantic-core` (strictly pinned at `2.41.5`) due to discovered `SystemError` incompatibility.

## [0.1.9] - 2026-04-07

### Verified
- Adversarial QA confirmed the structural soundness of the `_run_node` optimization. Eliminating closure allocations from the hot path maintained full system stability.

### Changed
- Entropy Pruned: 0 lines. Modernized type hints across `src/catalyst/domain/engine.py` using built-in generics (`dict`/`list`).
- Dependencies Bumped: Deferred upgrading `pydantic-core` (kept safely at `2.41.5`) due to a `SystemError` compatibility crash during adversarial testing.

## [0.1.8] - 2026-04-04

### Verified
- Adversarial QA confirmed that performance optimizations (like true parallel DAG execution and fail-fast short-circuiting) remain intact and tests run without blocking sibling nodes.

### Changed
- Entropy Pruned: 2 lines removed (cleaned up unneeded `print()` debugging statements in tests).
- Dependencies Bumped: Deferred upgrading `pydantic-core` (strictly pinned at `2.41.5`) due to `SystemError` compatibility issues.

## [0.1.7] - 2026-04-02

### Verified
- Adversarial QA confirmed proper asynchronous execution pathing for callables via `__call__` checking, and validated that refactored `_skip_result` execution maintains fast-fail guarantees using `asyncio.as_completed`.

### Changed
- Entropy Pruned: 0 lines (Maintained zero bloat; FastAPI endpoints ignored as false positives).
- Dependencies Bumped: Deferred upgrading `pydantic-core` (strictly pinned at `2.41.5`) due to discovered `SystemError` incompatibility with upstream Pydantic versions.


### Verified
- Adversarial QA confirmed that system-level interrupts (`asyncio.CancelledError`, `KeyboardInterrupt`, `SystemExit`) now safely propagate outwards after removing overly broad `BaseException` catching.

### Changed
- Entropy Pruned: 0 lines (FastAPI/Pydantic false positives ignored).
- Dependencies Bumped: Deferred upgrading `pydantic-core` 
... (truncated)