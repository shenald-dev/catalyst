We are given a merge conflict in CHANGELOG.md between base (main) and head (chore/optimize-execution-hot-path-3976356480118617981).
 The ancestor is the common base.

 We are to perform a 3-way merge and output the resolved file.

 Steps:
 1. We note that the base (main) has a newer version [0.1.30] at the top (from 2026-11-29) and then goes down to older versions.
 2. The head (PR branch) does not have [0.1.30] but has [0.1.29] (from 2026-05-28) and then older versions.

 However, note that the base (main) also has [0.1.29] (but with a different date? Actually, in base we see:
   ## [0.1.30] - 2026-11-29
   ... then later ...
   ## [0.1.29] - 2026-05-28   [This is in the base? Actually, looking at the base description:]

 But wait, the base (main) description says:
   Base (main): 222 lines changed (lines 3-247)
   and then shows:
        # Changelog
        
      - All notable changes to this project will be documented in this file.
      + ## [0.1.30] - 2026-11-29
      + * **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly.
      ... and so on.

 However, the head (PR branch) does not have [0.1.30] but starts with [0.1.29] (from 2026-05-28).

 Also note: the ancestor (common base) only had up to [0.1.25] (as per the ancestor snippet: "## [0.1.25] - 2026-05-07").

 Therefore, the base (main) has added:
   - [0.1.30] (2026-11-29)
   - and also modified the existing [0.1.29] (which in the ancestor was not present? Actually, the ancestor only went to 0.1.25, so [0.1.29] and [0.1.30] are both new in base?).

 But wait, the head (PR branch) also has [0.1.29] (with a different set of changes?).

 Let's break down:

 Ancestor: 
   ... up to [0.1.25] - 2026-05-07

 Base (main):
   Added [0.1.30] (2026-11-29) at the top.
   Then, it also has [0.1.29] (2026-05-28) and then [0.1.28], [0.1.27], ... down to [0.1.25] (which was in the ancestor) but with modifications.

 Head (PR branch):
   Does not have [0.1.30].
   Starts with [0.1.29] (2026-05-28) and then goes down to [0.1.25] (with modifications).

 Therefore, the conflict is that:
   - Base has added [0.1.30] at the top and modified the existing entries from [0.1.29] down to [0.1.25].
   - Head has modified the entries from [0.1.29] down to [0.1.25] (but did not add [0.1.30]).

 Since the base has [0.1.30] and the head does not, we must keep [0.1.30] from base.

 For the sections from [0.1.29] down to [0.1.25], both base and head have made changes. We must merge these sections by taking changes from both.

 However, note that the base and head have made changes to the same version sections (e.g., [0.1.29], [0.1.28], etc.). We have to combine the changes from both branches for each version section.

 Approach:
   We will start from the top (most recent) and go down.

   The base has:
      [0.1.30] (only in base)
      then [0.1.29] (with base's changes)
      then [0.1.28] (with base's changes)
      ... etc.

   The head has:
      [0.1.29] (with head's changes)
      then [0.1.28] (with head's changes)
      ... etc.

   We note that the ancestor did not have [0.1.29] or [0.1.30] (only up to [0.1.25]). Therefore, for [0.1.29] and [0.1.30], the base is the only one that added them? 
   But wait: the head also has [0.1.29] (so [0.1.29] was added by both branches?).

   Actually, the ancestor did not have [0.1.29] (it stopped at [0.1.25]). So both base and head added [0.1.29] independently? 
   However, looking at the diff provided for head changes vs base:

        @@ -1,7 +1,37 @@
         # Changelog
         
        +## [0.1.29] - 2026-05-28
        ...
        +## [0.1.28] - 2026-05-26
        ...

   This diff is showing that the head (PR branch) has added [0.1.29] and [0.1.28] etc. relative to the base? 
   But wait, the base already has [0.1.30] and then [0.1.29]? 

   Let me re-read the context:

   Base (main) description: 
        Base (main): 222 lines changed (lines 3-247)
        and then shows a diff that starts with:
            # Changelog
            
          - All notable changes to this project will be documented in this file.
          + ## [0.1.30] - 2026-11-29
          ... 

   This means that in the base, compared to the ancestor, they added [0.1.30] and then also modified the existing content (which was the ancestor's content) by inserting the new versions.

   Similarly, the head (PR branch) description says:
        Head (chore/optimize-execution-hot-path-3976356480118617981): 218 lines changed (lines 3-241)
        and then shows a diff that starts with:
            # Changelog
            
          - All notable changes to this project will be documented in this file.
          + ## [0.1.29] - 2026-05-28
          ...

   This means that in the head, compared to the ancestor, they added [0.1.29] and then modified the existing content (the ancestor's content) by inserting the new versions.

   However, note that the base already has [0.1.30] and then [0.1.29] (so the base has two new versions: 0.1.30 and 0.1.29, and then the old versions from the ancestor modified).

   The head has [0.1.29] and then the old versions from the ancestor modified.

   Therefore, for the version [0.1.29]:
        - Base has a set of changes for [0.1.29] (which we see in the base version)
        - Head has a set of changes for [0.1.29] (which we see in the head version)

   And we must merge these two sets of changes for [0.1.29] (and similarly for [0.1.28], [0.1.27], etc.).

   But note: the base also has [0.1.30] which the head does not have, so we must include [0.1.30] from base.

   How to merge a version section (e.g., [0.1.29])?
        We take the bullet points from both base and head for that version and combine them, avoiding duplicates.

   However, note that the same bullet point might appear in both? We have to avoid duplicating the same bullet.

   But the instructions say: "Keep ALL meaningful changes from BOTH branches"

   So we will take every bullet point that appears in either base or head for that version, and if the same bullet point appears in both, we only include it once.

   However, note that the bullet points might be slightly different (e.g., one has a typo fixed). We cannot do semantic merging, so we have to rely on the text.

   But note: the problem says "When both modify the same code: If they add different things (different imports, different functions), keep BOTH". 
   In this case, the bullet points are like "functions" (each bullet is a change). So if base has bullet A and head has bullet B for the same version, we keep both A and B.

   However, if base and head both have the exact same bullet point, we only keep one.

   Steps for merging:

   1. We will build the changelog from the most recent version to the oldest.

   2. We know the base has [0.1.30] (which head does not) -> so we start with [0.1.30] from base.

   3. Then for [0.1.29]: we take the union of the bullet points from base's [0.1.29] and head's [0.1.29].

   4. Similarly for [0.1.28], [0.1.27], ... down to [0.1.25].

   5. For versions older than [0.1.25] (i.e., [0.1.24] and below), note that the ancestor had them and both base and head have modified them? 
      Actually, the base and head both have modifications for versions from [0.1.25] down to the oldest.

      But note: the ancestor had [0.1.25] and older. The base and head both modified [0.1.25] and older.

      However, the base and head might have made different changes to the same older version.

      So for each version from [0.1.24] down, we take the union of the bullet points from base and head for that version.

   6. We must also note that the base and head might have added new version sections that the other doesn't have? 
      We already handled [0.1.30] (only in base) and [0.1.29] is in both? Actually, wait: the head does not have [0.1.30] but has [0.1.29] and the base has both [0.1.30] and [0.1.29].

      But note: the base's [0.1.29] and the head's [0.1.29] are two different sets of changes for the same version.

   However, there is a catch: the base and head might have reordered the versions? 
      We see that in the base, the versions are in descending order (from 0.1.30 down to 0.1.21 or so) and similarly in the head.

   We must maintain descending order (most recent first).

   How to get the bullet points for each version from the base and head?

   Unfortunately, we are not given the full files, but we are given the context of what changed in each branch (with truncation). 
   However, we are also given the Git Diff (Head changes vs base) which shows the changes that the head made relative to the base.

   But note: the problem says we are to resolve the merge conflict. We have three versions: ancestor, base, head.

   Since we don't have the full files, we must rely on the provided context and the diff.

   However, the problem also provides the full content of the ancestor, base, and head (but truncated in the middle). 
   We are expected to use the provided snippets to infer the changes.

   Given the complexity and the truncation, we must note that the problem expects us to use the provided information.

   Let's look at the provided Git Diff (Head changes vs base):

        @@ -1,7 +1,37 @@
         # Changelog
         
        +## [0.1.29] - 2026-05-28
        +* **[QA Status]:** Verified the structural soundness of `WorkflowEngine` and its fail-fast asynchronous evaluation. No regressions were found during test suite execution.
        +* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
        +* **[Dependencies Bumped]:** Safely bumped `idna`, `ruff`, and `starlette` to their latest minor/patch versions. Kept `mypy` constrained to `<2` to prevent breaking changes.
        +* **[Docs Updated]:** Logged system evaluation and safe dependency updates to `.jules/warden.md`.
        +* **[Release]:** v0.1.29 cut, tagged, and ready.
        +
         All notable changes to this project will be documented in this file.
         
        +## [0.1.28] - 2026-05-26
        +* **[QA Status]**: Verified. Checked BOLT's optimization passes across the test suite and engine hot paths. No anomalies detected.
        +* **[Entropy Pruned]**: -0 lines of dead code removed. The repository remains highly optimized and free of unused imports and variables.
        +* **[Dependencies Bumped]**: Upgraded click, coverage, fastapi, idna, pytest-asyncio, starlette, and uvicorn. Maintained mypy constraint to prevent CI failure.
        +* **[Docs Updated]**: Versioned `pyproject.toml`, FastAPI definitions, and synchronized architectural shifts in `.jules/warden.md`.
        +
        +## [0.1.27] - 2026-05-21
        +
        +### Changed
        +- **[Dependencies Bumped]:** Safely bumped `certifi` to `v2026.5.20`, `ruff` to `v0.15.14`, and `starlette` to `v1.0.1`.
        +- **[QA Status]:** Verified BOLT's fast-path optimization (`if deps else ()`) for task dependencies during DAG execution to eliminate tuple generator overhead. Passed strict static checks and fail-fast unit tests.
        +- **[Entropy Pruned]:** No structural dead code required pruning in this run (-0 lines).
        +
        +## [0.1.26] - 2026-05-12
        +
        +* **[QA Status]:** Verified structural soundness of the circular reference / memory leak fix within DAG evaluati

   This diff is showing that the head (PR branch) has, relative to the base, added:
        - [0.1.29] (with 6 bullets)
        - [0.1.28] (with 4 bullets)
        - [0.1.27] (with a "Changed" section and 3 bullets under it)
        - [0.1.26] (starts with a bullet but then truncated)

   But wait, the base already has [0.1.30] and then [0.1.29] (so the base has [0.1.29] as well). 
   This diff is head vs base, meaning:

        The base has:
            ... (we don't see the base's [0.1.29] in this diff because the diff is showing what the head added relative to base)

        Actually, the diff is: 
            - (lines removed from base) 
            + (lines added in head)

        So the head, compared to the base, has:
            - Removed the first 7 lines of the base (which were: 
                  # Changelog
                  
                  ## [0.1.30] - 2026-11-29
                  * **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly.
                  * **[Dependencies Bumped]:** Safely updated minor and patch dependencies in the lockfile.
                  * **[Entropy Pruned]:** -0 lines of dead code removed. Codebase is clean.
                  
                  ## [0.1.29] - 2026-05-28   [Wait, note: the base has [0.1.30] and then [0.1.29]?]

            But the diff shows:
                -1,7: meaning it removed 7 lines starting at line 1? 
                The base's first 7 lines are:
                    line1: "# Changelog"
                    line2: ""
                    line3: "## [0.1.30] - 2026-11-29"
                    line4: "* **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly."
                    line5: "* **[Dependencies Bumped]:** Safely updated minor and patch dependencies in the lockfile."
                    line6: "* **[Entropy Pruned]:** -0 lines of dead code removed. Codebase is clean."
                    line7: ""   [because then we see a blank line and then "## [0.1.29] - 2026-05-28" would be line8?]

            Actually, the base after the first 7 lines would have:
                    ## [0.1.29] - 2026-05-28
                    ... 

            So the head, relative to the base, has:
                - Removed the base's [0.1.30] section (7 lines: the header and 5 bullets and a blank line? Actually, the diff shows -1,7 meaning 7 lines removed from the base starting at line1)
                - And then added:
                      ## [0.1.29] - 2026-05-28
                      ... (6 bullets)
                      (blank line)
                      ## [0.1.28] - 2026-05-26
                      ... 
                      etc.

            This implies that the head does not have [0.1.30] at all, and instead of having [0.1.30] and then [0.1.29] (like the base), the head has [0.1.29] as the first version and then [0.1.28], etc.

   Therefore, to resolve:

        We want to keep:
          - The [0.1.30] section from the base (because the head doesn't have it, and it's a meaningful change from base).
          - Then, for the [0.1.29] section: we want to combine the base's [0.1.29] and the head's [0.1.29] (but note: the base's [0.1.29] is what was in the base after removing the first 7 lines? Actually, no: the base's [0.1.29] is still present in the base after the [0.1.30] section).

        However, the diff shows that the head removed the base's [0.1.30] and then replaced it with its own [0.1.29] and then the rest. 
        But the base's [0.1.29] is still present in the base (after [0.1.30]). 

        So in the base, we have:
            [0.1.30]
            [0.1.29]   (base's version of 0.1.29)
            [0.1.28]   (base's version of 0.1.28)
            ...

        In the head, we have (relative to base):
            Removed [0.1.30] and the base's [0.1.29]? 
            Actually, the diff shows removal of 7 lines (which we determined to be the [0.1.30] section and a blank line? or the [0.1.30] section and the first line of [0.1.29]?) 
            and then added its own [0.1.29] and then [0.1.28], etc.

        This is confusing.

   Let me try to reconstruct the base file from the context:

        Base (main) description says it changed lines 3-247, and shows:

            # Changelog
            
          - All notable changes to this project will be documented in this file.
          + ## [0.1.30] - 2026-11-29
          + * **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly.
          + * **[Dependencies Bumped]:** Safely updated minor and patch dependencies in the lockfile.
          + * **[Entropy Pruned]:** -0 lines of dead code removed. Codebase is clean.
          - 
          + * **[Entropy Pruned]:** 0 lines of dead code removed. Codebase is clean.
          - ## [0.1.25] - 2026-05-07
          + * **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly.
          - 
          + * **[Entropy Pruned]:** -0 lines of dead code removed. Codebase is clean.
          - * **[QA Status]**: Verified structural soundness of the `functools.partial` unwrapping optimization. The exact type checking (`type(...) is functools.partial`) was evaluated to safely handle the hot-path execution loop without introducing regressions or breaking fast-fail mechanisms.
          + 
          - * **[Entropy Pruned]**: 0 lines. Codebase remains at zero bloat, with FastAPI routing endpoints validated as false positives from `vulture` dead-code scans.
          + 
          - * **[Dependencies Bumped]**: Maintained core locked dependencies within `uv.lock`. Successfully rolled back `mypy` update to strictly adhere to `>=1.8.0,<2` constraint to avoid test failures.
          + ## [0.1.29] - 2026-05-28
          - * **[Docs Updated]**: Documented type checking micro-optimization guidelines in `.jules/warden.md` ledger.
          + 
          - * **[Release]**: v0.1.25 cut, tagged, and ready.
          + * **[QA Status]:** Verified the structural soundness of `WorkflowEngine` and its fail-fast asynchronous evaluation. No regressions were found during test suite execution.
          - 
          + * **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
          - ## [0.1.24] - 2026-05-05
          + * **[Dependencies Bumped]:** Safely bumped `idna`, `ruff`, and `starlette` to their latest minor/patch versions. Kept `mypy` constrained to `<2` to prevent breaking changes.
          - 
          + * **[Docs Updated]:** Logged system evaluation and safe dependency updates to `.jules/warden.md`.
          - * **[QA Status]:** Verified structural soundness of the codebase. The fast-fail mechanism correctly utilizes `asyncio.wait` ensuring no unawaited coroutines leak.
          - * **[Release]:** v0.1.29 cut, tagged, and ready.
          - * **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
          - + 
          - * **[Dependencies Bumped]:** Evaluated dependencies via `uv lock --upgrade`. Minor bumps passed perfectly.
          - - 
          - + * **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` ledger.
          - - All notable changes to this project will be documented in this file.
          - - * **[Release]:** v0.1.24 cut, tagged, and ready.
          - + 
          - - 
          - + ## [0.1.28] - 2026-05-26
          - - ## [0.1.23] - 2026-05-04
          - + * **[QA Status]**: Verified. Checked BOLT's optimization passes across the test suite and engine hot paths. No anomalies detected.
          - - 
          - + * **[Entropy Pruned]**: -0 lines of dead code removed. The repository remains highly optimized and free of unused imports and variables.
          - - * **[QA Status]:** Verified structural soundness of the codebase. The fast-fail mechanism utilizing `asyncio.wait` cleanly prevents coroutine leaks, and string dependency parsing remains robust against character destructuring.
          - - * **[Dependencies Bumped]**: Upgraded click, coverage, fastapi, idna, pytest-asyncio, starlette, and uvicorn. Maintained mypy constraint to prevent CI failure.
          - - * **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
          - - * **[Docs Updated]**: Versioned `pyproject.toml`, FastAPI definitions, and synchronized architectural shifts in `.jules/warden.md`.
          - - * **[Dependencies Bumped]:** Evaluated dependencies via `uv lock --upgrade` and maintained locked dependencies at their latest compatible versions.
          - - 
          - - * **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` ledger.
          - + ## [0.1.27] - 2026-05-21
          - - * **[Release]:** v0.1.23 cut, tagged, and ready.
          - + 
          - - 
          - + ### Changed
          - - ## [0.1.22] - 2026-05-03
          - + - **[Dependencies Bumped]:** Safely bumped `certifi` to `v2026.5.20`, `ruff` to `v0.15.14`, and `starlette` to `v1.0.1`.
          - - 
          - + - **[QA Status]:** Verified BOLT's fast-path optimization (`if deps else ()`) for task dependencies during DAG execution to eliminate tuple generator overhead. Passed strict static checks and fail-fast unit tests.
          - - * **[QA Status]:** Verified structural soundness of the fix for string dependency handling in `WorkflowEngine`. The codebase gracefully handles string inputs as single-element lists without destructing them.
          - + - **[Entropy Pruned]:** No structural dead code required pruning in this run (-0 lines).
          - - 
          - - * **[Dependencies Bumped]:** Maintained locked dependencies at their latest compatible versions.
          - + ## [0.1.26] - 2026-05-12
          - - * **[Docs Updated]:** Logged optimization and bugfix details in `warden.md` ledger.
          - + 
          - - * **[Release]:** v0.1.22 cut, tagged, and ready.
          - + * **[QA Status]:** Verified structural soundness of the circular reference / memory leak fix within DAG evaluation. Core tests pass seamlessly without introducing side effects.
          - - 
          - + * **[Entropy Pruned]:** 0 lines. Codebase zero-bloat state holds intact.
          - - ## [0.1.21] - 2026-05-01
          - + * **[Dependencies Bumped]:** Successfully locked `mypy<2` to preserve strict typing while allowing other dependencies to bump minor/patch versions safely via `uv lock --upgrade`.
          - - 
          - + * **[Docs Updated]:** Appended ledger record to `.jules/warden.md` validating the memory pipeline corrections.
          - - * **[QA Status]:** Verified structural soundness of the fix for string dependency handling in `WorkflowEngine`. The codebase gracefully handles string inputs as single-element lists without destructing them.
          - - * **[Release]:** v0.1.26 cut, tagged, and ready.
          - - * **[Entropy Pruned]:** 0 lines. Evaluated repository with `vulture`; remaining flags are properly confirmed as FastAPI external endpoints/false positives and left intact.
          - - 
          - - * **[Dependencies Bumped]:** Maintained locked dependencies at their latest compatible versions.
          - + ## [0.1.25] - 2026-05-07

        This is extremely messy and hard to follow.

   Given the complexity and the truncation, and since we are also given the Git Diff (Head changes vs base) which is clearer, let's use that.

   The Git Diff (Head changes vs base) shows:

        @@ -1,7 +1,37 @@
         # Changelog
         
        +## [0.1.29] - 2026-05-28
        +* **[QA Status]:** Verified the structural soundness of `WorkflowEngine` and its fail-fast asynchronous evaluation. No regressions were found during test suite execution.
        +* **[Entropy Pruned]:** 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
        +* **[Dependencies Bumped]:** Safely bumped `idna`, `ruff`, and `starlette` to their latest minor/patch versions. Kept `mypy` constrained to `<2` to prevent breaking changes.
        +* **[Docs Updated]:** Logged system evaluation and safe dependency updates to `.jules/warden.md`.
        +* **[Release]:** v0.1.29 cut, tagged, and ready.
        +
         All notable changes to this project will be documented in this file.
         
        +## [0.1.28] - 2026-05-26
        +* **[QA Status]**: Verified. Checked BOLT's optimization passes across the test suite and engine hot paths. No anomalies detected.
        +* **[Entropy Pruned]**: -0 lines of dead code removed. The repository remains highly optimized and free of unused imports and variables.
        +* **[Dependencies Bumped]**: Upgraded click, coverage, fastapi, idna, pytest-asyncio, starlette, and uvicorn. Maintained mypy constraint to prevent CI failure.
        +* **[Docs Updated]**: Versioned `pyproject.toml`, FastAPI definitions, and synchronized architectural shifts in `.jules/warden.md`.
        +
        +## [0.1.27] - 2026-05-21
        +
        +### Changed
        +- **[Dependencies Bumped]:** Safely bumped `certifi` to `v2026.5.20`, `ruff` to `v0.15.14`, and `starlette` to `v1.0.1`.
        +- **[QA Status]:** Verified BOLT's fast-path optimization (`if deps else ()`) for task dependencies during DAG execution to eliminate tuple generator overhead. Passed strict static checks and fail-fast unit tests.
        +- **[Entropy Pruned]:** No structural dead code required pruning in this run (-0 lines).
        +
        +## [0.1.26] - 2026-05-12
        +
        +* **[QA Status]:** Verified structural soundness of the circular reference / memory leak fix within DAG evaluati

   This diff is applied to the base to get the head.

   What does it mean?
        The base has, at the beginning:
            # Changelog
            
            ## [0.1.30] - 2026-11-29
            * **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly.
            * **[Dependencies Bumped]:** Safely updated minor and patch dependencies in the lockfile.
            * **[Entropy Pruned]:** -0 lines of dead code removed. Codebase is clean.
            
            ## [0.1.29] - 2026-05-28
            ... (we don't see the rest in the diff because the diff only shows the first 7 lines of base being removed and then 37 lines added)

        The head, therefore, has:
            # Changelog
            
            ## [0.1.29] - 2026-05-28   [with 6 bullets]
            (blank line)
            ## [0.1.28] - 2026-05-26   [with 4 bullets]
            (blank line)
            ## [0.1.27] - 2026-05-21   [with a "Changed" section and 3 bullets]
            (blank line)
            ## [0.1.26] - 2026-05-12   [starts with a bullet and then truncated]
            ... and then the rest of the file from the base starting at what was line 8 in the base? 

        But note: the diff says "+1,37" meaning it added 37 lines starting at line 1.

        And it removed 7 lines from the base starting at line 1.

        So the base's lines 1-7 are removed and replaced by 37 lines.

        What are the base's lines 1-7?
            Line 1: "# Changelog"
            Line 2: "" 
            Line 3: "## [0.1.30] - 2026-11-29"
            Line 4: "* **[QA Status]:** Verified. The latest parallel DAG execution improvements are structurally sound and handle faults properly."
            Line 5: "* **[Dependencies Bumped]:** Safely updated minor and patch dependencies in the lockfile."