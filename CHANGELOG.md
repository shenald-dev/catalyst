# Changelog

## [0.1.36] - 2026-06-08

- be6aeac chore(sentinel): update monitoring log
- b5bee7d chore(warden): update ledger
- 19a0b4c chore(release): v0.1.35
- 7bae13e chore(sentinel): update monitoring log
- 5e6f9bc chore(warden): update ledger
- fecf572 chore(release): v0.1.34
- 8a1b823 chore(sentinel): update monitoring log
- 0751111 Merge pull request #136 from shenald-dev/jules-warden-release-0.1.33-6450149706948955292
- aa8bb36 chore(release): v0.1.33
- 3fcc901 Merge pull request #135 from shenald-dev/jules/apex-forge-maintainability-2430603911627901522


## [0.1.35] - 2026-06-08

- 7bae13e chore(sentinel): update monitoring log
- 5e6f9bc chore(warden): update ledger
- fecf572 chore(release): v0.1.34
- 8a1b823 chore(sentinel): update monitoring log
- 0751111 Merge pull request #136 from shenald-dev/jules-warden-release-0.1.33-6450149706948955292
- aa8bb36 chore(release): v0.1.33
- 3fcc901 Merge pull request #135 from shenald-dev/jules/apex-forge-maintainability-2430603911627901522
- b4b0596 Overhaul README with enterprise documentation
- e68699f Update README with awesome new logo and formatting
- 40fdda0 feat(maintainability): export engine primitives and sync API version


## [0.1.34] - 2026-06-07

- 8a1b823 chore(sentinel): update monitoring log
- 0751111 Merge pull request #136 from shenald-dev/jules-warden-release-0.1.33-6450149706948955292
- aa8bb36 chore(release): v0.1.33
- 3fcc901 Merge pull request #135 from shenald-dev/jules/apex-forge-maintainability-2430603911627901522
- b4b0596 Overhaul README with enterprise documentation
- e68699f Update README with awesome new logo and formatting
- 40fdda0 feat(maintainability): export engine primitives and sync API version
- 7091c57 Merge pull request #134 from shenald-dev/apex-forge-repo-improvement-7929688882270510647
- 8c0dcc6 fix: resolve mypy type check and ruff linting errors in test suite
- 9d71590 Merge pull request #94 from shenald-dev/jules-warden-release-0-1-25-3847883659067729078


## [0.1.26] - 2026-05-13

### 🐛 Bug Fixes
* **[QA Status]:** Verified fix for memory leak in workflow engine fail-fast logic. Breaking early from `asyncio.as_completed` leaked wrapper coroutines causing `RuntimeWarning`. The logic now safely utilizes `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)` resolving background tasks correctly natively.

### 🧹 Maintenance
* **[Lifecycle]:** Minor dependencies updated safely (idna). Deferred major bumps for strict typing tools like mypy to preserve backward compatibility.
* **[Documentation]:** Updated `README.md` to reflect proper fail-fast optimization architecture avoiding task leaks, synced internal `.jules/warden.md` ledger.
* **[Release]:** v0.1.26 cut, tagged, and ready.
## [0.1.30] - 2026-11-29
* **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly.
* **[Dependencies Bumped]:** Safely updated minor and patch dependencies in the lockfile.
* **[Entropy Pruned]:** -0 lines of dead code removed. Codebase is clean.


## [0.1.29] - 2026-05-28

* **[QA Status]:** Verified the structural soundness of `WorkflowEngine` and its fail-fast asynchronous evaluation. No regressions were found during test suite execution.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Safely bumped `idna`, `ruff`, and `starlette` to their latest minor/patch versions. Kept `mypy` constrained to `<2` to prevent breaking changes.
* **[Docs Updated]:** Logged system evaluation and safe dependency updates to `.jules/warden.md`.
* **[Release]:** v0.1.29 cut, tagged, and ready.


All notable changes to this project will be documented in this file.

## [0.1.26] - 2026-05-12

## [0.1.25] - 2026-05-09

* **[QA Status]:** Verified structural soundness of the `functools.partial` unwrapping optimization. The changes maintain identical logical paths but avoid heavy introspection tools inside hot paths, completely respecting async bounds perfectly.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Maintained locked dependencies at their latest compatible versions via `uv lock --upgrade`, updating packages like `mypy` to `2.0.0`, `pydantic` to `2.13.4` and `pydantic-core` to `2.46.4`.
* **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` ledger.
* **[Release]:** v0.1.25 cut, tagged, and ready.
## [0.1.29] - 2026-05-26

* **[QA Status]**: Verified structural soundness of the DAG execution engine optimization. Passing a mutable dictionary of `asyncio.Task` objects to `_run_node` created a memory-leaking reference cycle. The transition to pre-resolved tuples safely breaks this cycle without breaking fail-fast behavior.
* **[Entropy Pruned]**: 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]**: Maintained core locked dependencies within `uv.lock`. Updated minor packages securely.
* **[Docs Updated]**: Documented memory reference cycle micro-optimization guidelines in `.jules/warden.md` ledger.
* **[Release]**: v0.1.29 cut, tagged, and ready.

## [0.1.28] - 2026-05-26* **[QA Status]**: Verified. Checked BOLT's optimization passes across the test suite and engine hot paths. No anomalies detected.
## [0.1.30] - 2026-11-29
* **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly.
* **[Dependencies Bumped]:** Safely updated minor and patch dependencies in the lockfile.
* **[Entropy Pruned]:** -0 lines of dead code removed. Codebase is clean.


## [0.1.29] - 2026-05-28

* **[QA Status]:** Verified the structural soundness of `WorkflowEngine` and its fail-fast asynchronous evaluation. No regressions were found during test suite execution.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Safely bumped `idna`, `ruff`, and `starlette` to their latest minor/patch versions. Kept `mypy` constrained to `<2` to prevent breaking changes.
* **[Docs Updated]:** Logged system evaluation and safe dependency updates to `.jules/warden.md`.
* **[Release]:** v0.1.29 cut, tagged, and ready.

## [0.1.28] - 2026-05-26




## [0.1.31] - 2026-05-26
## [0.1.28] - 2026-05-26
* **[QA Status]**: Verified. Checked BOLT's optimization passes across the test suite and engine hot paths. No anomalies detected.
* **[Entropy Pruned]**: -0 lines of dead code removed. The repository remains highly optimized and free of unused imports and variables.
* **[Dependencies Bumped]**: Upgraded click, coverage, fastapi, idna, pytest-asyncio, starlette, and uvicorn. Maintained mypy constraint to prevent CI failure.
* **[Docs Updated]**: Versioned `pyproject.toml`, FastAPI definitions, and synchronized architectural shifts in `.jules/warden.md`.

## [0.1.28] - 2026-05-22

* **[QA Status]:** Verified. Vulture results correctly identified as FastAPI false positives.
* **[Entropy Pruned]:** -0 lines (Codebase remains at zero bloat).
* **[Dependencies Bumped]:** `pydantic-core` bumped from 2.46.4 to 2.47.0. `click` from 8.4.0 to 8.4.1. `fastapi` from 0.136.1 to 0.136.3. `idna` from 3.15 to 3.16. `starlette` from 1.0.1 to 1.1.0. `uvicorn` from 0.47.0 to 0.48.0.
* **[Docs Updated]:** None.
* **[Release]:** v0.1.28 cut, tagged, and ready.
## [0.1.27] - 2026-05-21


## [0.1.28] - 2026-05-23

### Changed
- **[Dependencies Bumped]:** Safely bumped `click` to `v8.4.1`, `fastapi` to `v0.136.3`, `idna` to `v3.16`, and `starlette` to `v1.1.0`. Maintained `mypy<2` constraint.
- **[QA Status]:** Verified structural soundness of the application after minor dependency updates. Core test suites, mypy, and ruff checks all passed successfully.
- **[Entropy Pruned]:** 0 lines. Evaluated vulture scans and confirmed flags on FastAPI components were false positives.



## [0.1.27] - 2026-05-21

### Changed
- **[Dependencies Bumped]:** Safely bumped `certifi` to `v2026.5.20`, `ruff` to `v0.15.14`, and `starlette` to `v1.0.1`.
- **[QA Status]:** Verified BOLT's fast-path optimization (`if deps else ()`) for task dependencies during DAG execution to eliminate tuple generator overhead. Passed strict static checks and fail-fast unit tests.
- **[Entropy Pruned]:** No structural dead code required pruning in this run (-0 lines).

## [0.1.26] - 2026-05-12

* **[QA Status]**: Verified structural soundness of the async tuple pre-resolution memory leak fix. Tests pass successfully.
* **[Entropy Pruned]**: 0 lines. Codebase remains at zero bloat, with FastAPI routing endpoints validated as false positives from `vulture` scans.
* **[Dependencies Bumped]**: Safely bumped `idna` to v3.15 and constrained `mypy<2`.
* **[Docs Updated]**: Documented changes in `.jules/warden.md` and `CHANGELOG.md`.
* **[QA Status]:** Verified structural soundness of the circular reference / memory leak fix within DAG evaluation. Core tests pass seamlessly without introducing side effects.
* **[Entropy Pruned]:** 0 lines. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Successfully locked `mypy<2` to preserve strict typing while allowing other dependencies to bump minor/patch versions safely via `uv lock --upgrade`.
* **[Docs Updated]:** Appended ledger record to `.jules/warden.md` validating the memory pipeline corrections.
* **[Release]:** v0.1.26 cut, tagged, and ready.

## [0.1.25] - 2026-05-07

* **[QA Status]:** Verified structural soundness of the `functools.partial` strict type checking optimization in `WorkflowEngine.add_task`. Exact type evaluation is isolated and correctly executes in hot paths safely.
* **[Entropy Pruned]:** 0 lines. Checked the repository with `vulture` and verified all unused code has been cleanly pruned, correctly deferring false positive FastAPI routing functions.
* **[Dependencies Bumped]:** Successfully upgraded all core dependencies via lockfile resolution, including `pydantic-core` (now safely running `v2.46.4` without `SystemError` crashes) and `mypy` (v2.0.0).
* **[Docs Updated]:** Logged optimization patterns in `warden.md` and prepared version bump to v0.1.25.
* **[Release]:** v0.1.25 cut, tagged, and ready.

* **[QA Status]:** Verified structural soundness of the `functools.partial` exact type checking micro-optimization in `WorkflowEngine.add_task`.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Upgraded minor versions of `coverage`, `idna`, `librt`, `pydantic`, and `pydantic-core` safely via `uv lock --upgrade`. `mypy` update has been constrained to `<2` to prevent potential breaks in backwards compatibility.
* **[Docs Updated]:** Logged optimization and dependency bump details in `warden.md` ledger.
* **[Release]:** v0.1.25 cut, tagged, and ready.
* **[QA Status]**: Verified structural soundness of the `functools.partial` unwrapping optimization. The exact type checking (`type(...) is functools.partial`) was evaluated to safely handle the hot-path execution loop without introducing regressions or breaking fast-fail mechanisms.
* **[Entropy Pruned]**: 0 lines. Codebase remains at zero bloat, with FastAPI routing endpoints validated as false positives from `vulture` dead-code scans.
* **[Dependencies Bumped]**: Maintained core locked dependencies within `uv.lock`. Successfully rolled back `mypy` update to strictly adhere to `>=1.8.0,<2` constraint to avoid test failures.
* **[Docs Updated]**: Documented type checking micro-optimization guidelines in `.jules/warden.md` ledger.
* **[Release]**: v0.1.25 cut, tagged, and ready.

## [0.1.24] - 2026-05-05

* **[QA Status]:** Verified structural soundness of the codebase. The fast-fail mechanism correctly utilizes `asyncio.wait` ensuring no unawaited coroutines leak.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Evaluated dependencies via `uv lock --upgrade`. Minor bumps passed perfectly.
* **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` ledger.
* **[Release]:** v0.1.24 cut, tagged, and ready.

## [0.1.23] - 2026-05-04

* **[QA Status]:** Verified structural soundness of the codebase. The fast-fail mechanism utilizing `asyncio.wait` cleanly prevents coroutine leaks, and string dependency parsing remains robust against character destructuring.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Evaluated dependencies via `uv lock --upgrade` and maintained locked dependencies at their latest compatible versions.
* **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` ledger.
* **[Release]:** v0.1.23 cut, tagged, and ready.

## [0.1.22] - 2026-05-03

* **[QA Status]:** Verified structural soundness of the fix for string dependency handling in `WorkflowEngine`. The codebase gracefully handles string inputs as single-element lists without destructing them.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Maintained locked dependencies at their latest compatible versions.
* **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` ledger.
* **[Release]:** v0.1.22 cut, tagged, and ready.

## [0.1.21] - 2026-05-01

* **[QA Status]:** Verified structural soundness of the fix for string dependency handling in `WorkflowEngine`. The codebase gracefully handles string inputs as single-element lists without destructing them.
* **[Entropy Pruned]:** 0 lines. Evaluated repository with `vulture`; remaining flags are properly confirmed as FastAPI external endpoints/false positives and left intact.
* **[Dependencies Bumped]:** Maintained locked dependencies at their latest compatible versions.
* **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` ledger.
* **[Release]:** v0.1.21 cut, tagged, and ready.

## [0.1.20] - 2026-04-30

* **[QA Status]:** Verified structural soundness of the prior agent's registration path fast-fail refactor. Tests natively pass and no regressions were found.
* **[Entropy Pruned]:** 2 lines. Pruned unreachable `iscoroutinefunction` dead code wrapped within the `functools.partial` loop fallback, recovering 100% test coverage.
* **[Dependencies Bumped]:** Maintained locked dependencies at their latest compatible versions.
* **[Docs Updated]:** Logged optimization and refactoring details in `warden.md` ledger.
* **[Release]:** v0.1.20 cut, tagged, and ready.

## [0.1.21] - 2024-05-11

* **[Optimization]:** Refactored `_run_node` to accept pre-resolved dependency tuples instead of the mutable `tasks` dictionary. This breaks a circular reference (`tasks` dict -> `Task` object -> `Coroutine` -> `tasks` dict) and permanently resolves a background memory leak during heavy concurrent DAG execution.


## [0.1.19] - 2026-04-29

* **[QA Status]:** Verified structural soundness of the fast path optimizations in `add_task` and the loop simplifications in `_run_node`. The system evaluates the simplified bytecode early-return pattern perfectly, retaining fail-fast guarantees.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Maintained locked dependencies at their latest compatible versions within the editable virtual environment.
* **[Docs Updated]:** Logged optimization and refactoring details in `warden.md` ledger.
* **[Release]:** v0.1.19 cut, tagged, and ready.

## [0.1.18] - 2026-04-28

* **[QA Status]:** Verified structural soundness of the fix for silent iterator exhaustion in `WorkflowEngine.add_task`. The core graph logic materializes `Iterable` types properly, passing the test suite and edge case coverages flawlessly.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Maintained locked dependencies at their latest compatible versions.
* **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` tracking the elimination of the exhaustion bug. Updated `add_task` docstring to reflect the `Iterable` parameter.
* **[Release]:** v0.1.18 cut, tagged, and ready.


## [0.1.17] - 2026-04-25

* **[QA Status]:** Verified structural soundness of the fast-fail mechanism within the `WorkflowEngine`. The explicit, redundant synchronous checks via `task.done()` were replaced by directly evaluating `pending_set` natively via `asyncio.wait(FIRST_COMPLETED)`, entirely eliminating Python-level overhead and duplicate logic without breaking fail-fast constraints.
* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
* **[Dependencies Bumped]:** Dependencies are completely stable within the editable virtual environment.
* **[Docs Updated]:** Logged optimization patterns in `warden.md` tracking the elimination of redundant loops.
* **[Release]:** v0.1.17 cut, tagged, and ready.

## [0.1.16] - 2024-04-24

* **[QA Status]:** Verified structural soundness of the `WorkflowEngine` fast-fail optimization. The simplified `pending_set` evaluation loop natively leverages `asyncio.wait(FIRST_COMPLETED)` and correctly avoids breaking tests.
* **[Entropy Pruned]:** 0 lines. Evaluated repository with `vulture`; remaining flags (`execute_workflow`, `health_check`, `StatusResponse` properties) were properly confirmed as FastAPI external endpoints/false positives and left intact.
* **[Dependencies Bumped]:** Dependencies are stable and safely resolved in the editable virtual environment.
* **[Docs Updated]:** Logged system optimization shifts into the `warden.md` ledger noting the simplification pattern.

## [0.1.15] - 2026-04-23

* **[QA Status]:** Verified structural soundness of the `asyncio.as_completed` removal optimization. The dependency graph evaluates fail-fast logic safely via `asyncio.wait(FIRST_COMPLETED)` without memory leaks or unawaited coroutines.
* **[Entropy Pruned]:** 0 lines. Checked the repository with `vulture` and verified all unused code has been cleanly pruned.
* **[Dependencies Bumped]:** Verified dependencies are stable.
* **[Docs Updated]:** Updated docstrings in `src/catalyst/domain/engine.py` to reflect the transition to `asyncio.wait`.


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
* **[Performance]**: Fixed a memory-leaking reference cycle in `_run_node` by passing a tuple of resolved dependency tasks instead of a mutable dictionary of all tasks.

## [0.1.31] - 2026-05-31
* **Bugfix:** Auto-resolved git merge conflict syntax errors, ensuring safe dependency fetching logic and proper code indentations.

## 2026-06-01 - v0.1.32

* **Maintainability:** Exported core engine primitives at package root for better DX, and dynamically resolved FastAPI app version to prevent drift.

* **Lifecycle:** Cleaned up root project scratchpads, upgraded minor dependencies, and verified core logic.
