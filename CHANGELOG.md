# Changelog

All notable changes to this project will be documented in this file.

## [0.1.6] - 2026-04-01

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
