# Changelog

All notable changes to this project will be documented in this file.

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
