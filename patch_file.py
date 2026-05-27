import sys

def patch_file(filepath, search, replace):
    with open(filepath, 'r') as f:
        content = f.read()
    if search in content:
        content = content.replace(search, replace)
        with open(filepath, 'w') as f:
            f.write(content)
        print("Patched successfully!")
    else:
        print("Search string not found.")
        sys.exit(1)

patch_file(
    'CHANGELOG.md',
    '''<<<<<<< HEAD
## [0.1.28] - 2026-05-22

* **[QA Status]:** Verified. Vulture results correctly identified as FastAPI false positives.
* **[Entropy Pruned]:** -0 lines (Codebase remains at zero bloat).
* **[Dependencies Bumped]:** `pydantic-core` bumped from 2.46.4 to 2.47.0. `click` from 8.4.0 to 8.4.1. `fastapi` from 0.136.1 to 0.136.3. `idna` from 3.15 to 3.16. `starlette` from 1.0.1 to 1.1.0. `uvicorn` from 0.47.0 to 0.48.0.
* **[Docs Updated]:** None.
* **[Release]:** v0.1.28 cut, tagged, and ready.
=======
## [0.1.28] - 2026-05-26
* **[QA Status]**: Verified. Checked BOLT's optimization passes across the test suite and engine hot paths. No anomalies detected.
* **[Entropy Pruned]**: -0 lines of dead code removed. The repository remains highly optimized and free of unused imports and variables.
* **[Dependencies Bumped]**: Upgraded click, coverage, fastapi, idna, pytest-asyncio, starlette, and uvicorn. Maintained mypy constraint to prevent CI failure.
* **[Docs Updated]**: Versioned `pyproject.toml`, FastAPI definitions, and synchronized architectural shifts in `.jules/warden.md`.
>>>>>>> origin/main''',
    '''## [0.1.28] - 2026-05-26

* **[QA Status]**: Verified. Checked BOLT's optimization passes across the test suite and engine hot paths. No anomalies detected.
* **[Entropy Pruned]**: -0 lines of dead code removed. The repository remains highly optimized and free of unused imports and variables.
* **[Dependencies Bumped]**: Upgraded click, coverage, fastapi, idna, pytest-asyncio, starlette, and uvicorn. Maintained mypy constraint to prevent CI failure.
* **[Docs Updated]**: Versioned `pyproject.toml`, FastAPI definitions, and synchronized architectural shifts in `.jules/warden.md`.

## [0.1.28] - 2026-05-22

* **[QA Status]:** Verified. Vulture results correctly identified as FastAPI false positives.
* **[Entropy Pruned]:** -0 lines (Codebase remains at zero bloat).
* **[Dependencies Bumped]:** `pydantic-core` bumped from 2.46.4 to 2.47.0. `click` from 8.4.0 to 8.4.1. `fastapi` from 0.136.1 to 0.136.3. `idna` from 3.15 to 3.16. `starlette` from 1.0.1 to 1.1.0. `uvicorn` from 0.47.0 to 0.48.0.
* **[Docs Updated]:** None.
* **[Release]:** v0.1.28 cut, tagged, and ready.'''
)
