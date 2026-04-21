# Changelog

All notable changes to this project will be documented in this file.

## [0.1.14] - 2026-04-21

### Verified
- Adversarial QA confirmed structural soundness of the recent standard library `graphlib` optimizations. The dependency graph executes fast-fail logic correctly. The codebase maintains strict zero bloat.

### Changed
- Entropy Pruned: 0 lines. Checked the repository with `vulture` and verified all unused code has been cleanly pruned.
- Dependencies Bumped: Safely verified that the latest minor upgrades of core frameworks pass the test suite perfectly.


## [0.1.13] - 2026-04-20

### Verified
- Adversarial QA confirmed structural soundness of the `graphlib` migration. The internal Directed Graph functions flawlessly without external dependencies. The codebase maintains zero bloat.

### Changed
- Entropy Pruned: 0 lines. Replaced the `networkx` dependency with standard library elements (`graphlib.TopologicalSorter` and native dictionaries).
- Dependencies Bumped: Safely verified all tests pass without the `networkx` dependency.

## [0.1.12] - 2024-04-17

### Fixed
- Fixed an `asyncio.gather` background task leak. When a workflow evaluation task encounters a `BaseException` (like `SystemExit` or `KeyboardInterrupt`), the execution engine now gracefully iterates and issues `.cancel()` to any unawaited background sibling tasks instead of silently allowing them to drift and crash as orphans.

### Changed
- Entropy Pruned: 0 lines.
- Dependencies Bumped: Upgraded `mypy` locally; core boundaries remain intact.

## [0.1.11] - 2026-04-16

### Verified
- Adversarial QA confirmed structural soundness of the `WorkflowEngine.add_task()` bugfix. The internal Directed Graph is completely clear of stale incoming edges on task overwrite, maintaining true topological ordering without false cyclic errors.

### Changed
- Entropy Pruned: 0 lines.
- Dependencies Bumped: Successfully upgraded all core dependencies including `pydantic-core` (now safely running latest without `SystemError` crashes).

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
- Dependencies Bumped: Deferred upgrading `pydantic-core` (kept at `2.41.5`) due to incompatibility.

## [0.1.5] - 2026-03-31

### Verified
- Adversarial QA confirmed that `asyncio.wait(FIRST_COMPLETED)` gracefully manages background task completion and avoids memory leaks without breaking fast-fail constraints.

### Changed
- Entropy Pruned: 0 lines (codebase maintains zero bloat).
- Dependencies Bumped: Deferred upgrading `pydantic-core` (kept at `2.41.5`) due to incompatibility with FastAPI/pydantic tests.

## [0.1.4] - 2026-03-30

### Fixed
- Memory Leak: Replaced `asyncio.as_completed` with `asyncio.wait(FIRST_COMPLETED)` in the true fail-fast dependency evaluation loop, ensuring tasks are cleaned up immediately when short-circuiting to avoid "Task destroyed but it is pending" warnings.

## [0.1.3] - 2026-03-29

### Added
- Adversarial QA Test: Added tests for `timeout`, `__repr__` of TaskError, and detection of circular graph (`nx.NetworkXUnfeasible`) to ensure full structural coverage.

### Changed
- Pruned Dead Entropy: Rolled back `pydantic-core` dependency from 2.44.0 to 2.41.5 to maintain compatibility with `pydantic` in tests.

## [0.1.2] - 2026-03-28

### Added
- Adversarial QA Test: Added `test_fast_fail_does_not_cancel_unrelated_tasks` to ensure parallel fast-failure optimization does not leak execution cancellation to independent successful siblings.

### Changed
- Pruned Dead Entropy: Deleted unused `src/catalyst/infrastructure/` directory to maintain zero bloat.
- Bumped project dependencies to safe latest minor/patch versions.

## [0.1.1] - 2026-03-27

### Added
- Graceful API Execution Reporting: `TaskError` exceptions returned by the `execute_workflow` endpoint will now be correctly serialized as standard JSON, rather than crashing FastAPI.

### Changed
- Fail-Fast Optimization: Upgraded the DAG execution logic in `_run_node` to fast-fail the moment a sibling dependency produces a `TaskError`, skipping the task instead of sequentially awaiting all the rest before skipping. This cuts down overhead in wide, failing task nodes.
