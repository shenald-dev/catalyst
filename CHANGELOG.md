We are given a merge conflict in CHANGELOG.md between base (main) and head (warden-lifecycle-release-0.1.26-3960814560899493620).
 The ancestor is the common base.

 We are to perform a 3-way merge and output the resolved file.

 Steps:
 1. We note that the base (main) has a section for [0.1.27] - 2026-05-21 and then older versions.
 2. The head (PR branch) has a section for [0.1.27] - 2026-05-20 and then [0.1.26] - 2026-05-12, and then older versions.

 However, note that the base (main) also has a section for [0.1.26] - 2026-05-12? Actually, looking at the base (main) diff provided in the context:

 Base (main) changes (from the context):
   - It changed the version from [0.1.25] to [0.1.27] (with date 2026-05-21) and then added a "### Changed" section under [0.1.27].
   - Then it has a section for [0.1.26] - 2026-05-12 (which was added in the base) and then [0.1.25] - 2026-05-07, etc.

 But wait, the base (main) as shown in the context has:
   ## [0.1.27] - 2026-05-21
   ### Changed
   ... (some items)

   ## [0.1.26] - 2026-05-12
   ... (items)

   ## [0.1.25] - 2026-05-07
   ... (items)

   and so on.

 The head (PR branch) as shown in the context has:
   ## [0.1.27] - 2026-05-20
   ... (items)

   ## [0.1.26] - 2026-05-12
   ... (items)

   ## [0.1.25] - 2026-05-07
   ... (items)

   and so on.

 The conflict is that both branches have added a new version section at the top, but with different dates and slightly different content.

 Specifically:
   Base (main) has [0.1.27] - 2026-05-21
   Head (PR branch) has [0.1.27] - 2026-05-20

 Also, note that the base (main) has a "### Changed" subsection under [0.1.27] while the head (PR branch) does not (it uses bullet points directly).

 However, looking at the provided Git Diff (Head changes vs base) we see:

   The head (PR branch) has added:
        ## [0.1.27] - 2026-05-20
        * [QA Status]: ... (about DAG execution engine optimization)
        * [Entropy Pruned]: 0 lines ...
        * [Dependencies Bumped]: ... (Updated minor packages securely)
        * [Docs Updated]: ... (Documented memory reference cycle micro-optimization guidelines)
        * [Release]: v0.1.27 cut, tagged, and ready.

        ## [0.1.26] - 2026-05-12
        * [QA Status]: ... (circular reference / memory leak fix)
        * [Entropy Pruned]: 0 lines ...
        * [Dependencies Bumped]: ... (Successfully locked mypy<2 ...)
        * [Docs Updated]: ... (Appended ledger record ...)
        * [Release]: v0.1.26 cut, tagged, and ready.

   And then it has the existing [0.1.25] section (which is the same as in the base?).

 But note: the base (main) also has a [0.1.26] section and a [0.1.25] section, but with different content.

 How to resolve:

 We are to keep ALL meaningful changes from both branches.

 Since both branches have added a new version at the top (0.1.27) but with different dates and different content, we must combine them.

 However, note that the version number is the same (0.1.27) but the dates are different. We cannot have two sections for the same version.

 We must decide which date to use? But note: the base (main) has 2026-05-21 and the head has 2026-05-20.

 Since the head is the PR branch and we are merging into base (main), and the base (main) already has a [0.1.27] section (with date 2026-05-21), we should keep the base's version? 
 But wait, the head also has a [0.1.27] section (with date 2026-05-20) and then a [0.1.26] section.

 However, the base (main) also has a [0.1.26] section (which the head also has) and then the base (main) has [0.1.25] and so on.

 The problem: both branches have added a new version (0.1.27) but with different dates and different content.

 We must combine the changes from both branches for the same version? But note: the base (main) has a [0.1.27] section that the head does not have (because the head has [0.1.27] but with a different date and content) and vice versa.

 Actually, the base (main) and head both have a section for 0.1.27, but they are different.

 How to handle:

 Since the version number is the same, we should merge the content of the two 0.1.27 sections.

 But note: the base (main) has:
   ## [0.1.27] - 2026-05-21
   ### Changed
   - [Dependencies Bumped]: ... (certifi, ruff, starlette)
   - [QA Status]: ... (BOLT's fast-path optimization)

 The head (PR branch) has:
   ## [0.1.27] - 2026-05-20
   * [QA Status]: ... (DAG execution engine optimization)
   * [Entropy Pruned]: 0 lines ...
   * [Dependencies Bumped]: ... (Updated minor packages securely)
   * [Docs Updated]: ... (Documented memory reference cycle micro-optimization guidelines)
   * [Release]: v0.1.27 cut, tagged, and ready.

 We are to keep all meaningful changes from both branches.

 However, note that the base (main) has a "### Changed" subsection and the head does not. We should preserve the markdown structure.

 But the head does not use a "### Changed" subsection, it uses bullet points directly under the version.

 We have two options:
   Option 1: Keep the base's structure (with ### Changed) and add the head's items under that subsection? 
   Option 2: Or, since the head does not have a subsection, we might consider that the head's section is formatted differently.

 However, looking at the rest of the changelog, it seems that the sections under a version are either:
   - A list of bullet points (without a subsection) OR
   - With subsections (like ### Changed, ### Added, etc.)

 In the base (main) for [0.1.27] we see a ### Changed subsection.

 In the head (PR branch) for [0.1.27] we see bullet points without a subsection.

 But note: the base (main) also has for [0.1.26] and [0.1.25] etc. without subsections? Actually, in the base (main) context we see:

   ## [0.1.26] - 2026-05-12
   ... (bullet points without a subsection)

   ## [0.1.25] - 2026-05-07
   ... (bullet points without a subsection)

 So the base (main) has inconsistent formatting for [0.1.27] (it has a ### Changed subsection) while the others do not.

 This might be a mistake in the base (main). However, we are to merge the changes.

 Since the head (PR branch) does not use a subsection for [0.1.27] and the base (main) does, we must decide.

 But note: the base (main) is the target branch and we are merging the head into it. The base (main) already has the ### Changed subsection for [0.1.27]. 
 We should keep that and then add the head's changes appropriately.

 However, the head's changes for [0.1.27] are not under a subsection. We can either:
   - Add the head's changes as bullet points under the ### Changed subsection? 
   - Or, change the base (main) to remove the ### Changed subsection and just have bullet points? 

 But the rules say: keep ALL meaningful changes from both branches.

 The base (main) has introduced a ### Changed subsection and two items under it.
 The head (PR branch) has introduced five items (without a subsection) for [0.1.27].

 We cannot have two different formats for the same version.

 Let's look at the rest of the changelog: the other versions (like 0.1.26, 0.1.25) do not have subsections. They are just bullet points.

 Therefore, to be consistent, we should probably remove the ### Changed subsection and just have bullet points for [0.1.27] as well.

 However, note that the base (main) might have intended to use subsections. But since the other sections don't, and the head doesn't, we follow the existing pattern of the file (which is without subsections for the version sections).

 But wait: the base (main) as provided in the context for [0.1.27] has a ### Changed subsection. However, the ancestor did not have [0.1.27] at all.

 Since the base (main) is the target and we are merging, we have to decide.

 However, the problem says: "Keep ALL meaningful changes from BOTH branches"

 The base (main) change for [0.1.27] includes the ### Changed subsection and two items.
 The head (PR branch) change for [0.1.27] includes five items (without a subsection).

 We can interpret that the base (main) intended to structure the [0.1.27] section with a ### Changed subsection, but the head (PR branch) did not.

 Since the rest of the file (for other versions) does not use subsections, it is likely that the base (main) made a mistake by adding the ### Changed subsection.

 But note: the base (main) also has for [0.1.26] and [0.1.25] etc. without subsections, so the ### Changed subsection in [0.1.27] is an anomaly.

 How have other sections been formatted? Let's look at the ancestor.

 The ancestor (common base) had:
   ## [0.1.25] - 2026-05-07
   * [QA Status]: ... (truncated)

 So the ancestor did not use subsections.

 Therefore, we should not use subsections in the version sections.

 So we will remove the ### Changed subsection from the base (main)'s [0.1.27] section and treat its items as bullet points.

 Then, we can combine the bullet points from the base (main) and the head (PR branch) for [0.1.27].

 Steps for [0.1.27]:
   Base (main) items (after removing the ### Changed):
        - **[Dependencies Bumped]:** Safely bumped `certifi` to `v2026.5.20`, `ruff` to `v0.15.14`, and `starlette` to `v1.0.1`.
        - **[QA Status]:** Verified BOLT's fast-path optimization (`if deps else ()`) for task dependencies during DAG execution to eliminate tuple generator overhead. Passed strict static checks and fail-fast unit tests.

   Head (PR branch) items:
        * **[QA Status]**: Verified structural soundness of the DAG execution engine optimization. Passing a mutable dictionary of `asyncio.Task` objects to `_run_node` created a memory-leaking reference cycle. The transition to pre-resolved tuples safely breaks this cycle without breaking fail-fast behavior.
        * **[Entropy Pruned]**: 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
        * **[Dependencies Bumped]**: Maintained core locked dependencies within `uv.lock`. Updated minor packages securely.
        * **[Docs Updated]**: Documented memory reference cycle micro-optimization guidelines in `.jules/warden.md` ledger.
        * **[Release]**: v0.1.27 cut, tagged, and ready.

 We note that the base (main) has two items and the head has five.

 We must keep all.

 However, note that the base (main) item for [QA Status] is about BOLT's fast-path optimization, and the head has a [QA Status] item about DAG execution engine optimization. They are different.

 Also, the base (main) has a [Dependencies Bumped] item and the head has a [Dependencies Bumped] item (but different content).

 We will combine them.

 But note: the head (PR branch) also has a [Release] item. The base (main) does not have a [Release] item in its [0.1.27] section? 
 Actually, the base (main) does not show a [Release] item for [0.1.27] in the provided context. However, looking at the base (main) context, we see:

   ## [0.1.27] - 2026-05-21
   ### Changed
   ... (two items)

   and then it goes to ## [0.1.26] - 2026-05-12

 So the base (main) does not have a [Release] item for [0.1.27]. But the head (PR branch) does.

 We should include the [Release] item from the head.

 Now, what about the date? We have two different dates: 2026-05-21 (base) and 2026-05-20 (head).

 We must choose one. Since the base (main) is the target branch and we are merging the head into it, and the base (main) already has a date, we might keep the base's date? 
 But note: the head (PR branch) is the one that is trying to release 0.1.27 on 2026-05-20, and the base (main) has 2026-05-21.

 However, the base (main) might have been updated after the head was branched? 

 Since we are doing a 3-way merge and we are to keep all changes, we cannot have two dates.

 We note that the head (PR branch) has a [0.1.26] section that the base (main) also has (but with different content). 

 How about we look at the order of versions? The versions should be in descending order.

 The base (main) has:
   0.1.27 (2026-05-21)
   0.1.26 (2026-05-12)
   0.1.25 (2026-05-07)
   ...

 The head (PR branch) has:
   0.1.27 (2026-05-20)
   0.1.26 (2026-05-12)
   0.1.25 (2026-05-07)
   ...

 So the only difference is the date for 0.1.27.

 We must decide on the date. Since the base (main) is the target and we are merging the head into it, and the base (main) already has a date for 0.1.27, we keep the base's date? 
 But note: the head (PR branch) is the one that is introducing the 0.1.27 release (with a specific set of changes) and the base (main) has a different set of changes for 0.1.27.

 However, the base (main) might have been updated by someone else after the head was branched? 

 Since we are to keep all changes, we should keep the changes from both branches. But the date is part of the version header.

 We cannot have two dates. We must choose one.

 Let's see the Git Diff (Head changes vs base): it shows that the head added a [0.1.27] section with date 2026-05-20 and then a [0.1.26] section, etc.

 The base (main) has a [0.1.27] section with date 2026-05-21.

 Since the base (main) is the target and we are merging the head into it, and the base (main) already has a [0.1.27] section, we will keep the base's date for the version header? 
 But then we lose the head's date? 

 Alternatively, we note that the head (PR branch) is the one that is trying to add the 0.1.27 release, and the base (main) might have mistakenly added a 0.1.27 release with a future date? 

 However, without more context, we follow the rule: when both modify the same line (or in this case, the same version header), we prefer the HEAD branch (PR author's intent) unless the base has an obvious bug fix or security patch.

 The base (main) change for the [0.1.27] header is just changing the date from 0.1.25 to 0.1.27 and setting the date to 2026-05-21. 
 The head (PR branch) change for the [0.1.27] header is setting the date to 2026-05-20.

 There's no obvious bug fix or security patch in either. So we prefer the HEAD branch (PR branch) for the date? 

 But note: the base (main) also changed the content under [0.1.27] (adding the ### Changed subsection and two items). The head (PR branch) also added content under [0.1.27] (five items).

 We are to keep all changes from both branches. So we will combine the content and use the date from the head (PR branch) because the head is the PR branch and we prefer it in case of conflict (unless base has obvious bug fix, which it doesn't).

 However, wait: the base (main) is the target branch and we are merging the head into it. The base (main) already has the version header for 0.1.27 with date 2026-05-21. 
 The head (PR branch) is trying to change that header to 2026-05-20 and add its own content.

 Since we are to keep all changes, we must incorporate the head's changes. The head's change includes changing the date to 2026-05-20 and adding five items.

 The base (main) change includes changing the date to 2026-05-21 and adding two items (under a ### Changed subsection, which we are going to remove to be consistent).

 We decide to use the head's date (2026-05-20) for the version header because:
   - The head (PR branch) is the one that is introducing the 0.1.27 release (with its set of changes) and the base (main) might have been a mistake? 
   - But note: the base (main) also has a 0.1.27 release. 

 However, the base (main) might have been updated by another PR that was merged before this one? 

 Since we don't have that context, and the problem says to prefer the HEAD branch (PR author's intent) when they modify the same logic and there's no obvious bug fix in the base, we will use the head's date.

 But note: the base (main) change is not just the date, it also added two items. We are going to keep those two items (as bullet points) and add the head's five items.

 So the [0.1.27] section will have:
   ## [0.1.27] - 2026-05-20
   * [Dependencies Bumped]: Safely bumped `certifi` to `v2026.5.20`, `ruff` to `v0.15.14`, and `starlette` to `v1.0.1`.   [from base]
   * [QA Status]: Verified BOLT's fast-path optimization (`if deps else ()`) for task dependencies during DAG execution to eliminate tuple generator overhead. Passed strict static checks and fail-fast unit tests.   [from base]
   * [QA Status]: Verified structural soundness of the DAG execution engine optimization. ...   [from head]
   * [Entropy Pruned]: 0 lines. ...   [from head]
   * [Dependencies Bumped]: Maintained core locked dependencies within `uv.lock`. Updated minor packages securely.   [from head]
   * [Docs Updated]: Documented memory reference cycle micro-optimization guidelines in `.jules/warden.md` ledger.   [from head]
   * [Release]: v0.1.27 cut, tagged, and ready.   [from head]

 However, note that we have two [Dependencies Bumped] items and two [QA Status] items. That's acceptable.

 But wait: the base (main) item for [Dependencies Bumped] is about bumping certifi, ruff, and starlette, and the head (PR branch) item for [Dependencies Bumped] is about updating minor packages securely. They are different.

 Now, what about the [0.1.26] section?

 The base (main) has:
   ## [0.1.26] - 2026-05-12
   * [QA Status]: Verified structural soundness of the circular reference / memory leak fix within DAG evaluation. Core tests pass seamlessly without introducing side effects.
   * [Entropy Pruned]: 0 lines. Codebase zero-bloat state holds intact.
   * [Dependencies Bumped]: Successfully locked `mypy<2` to preserve strict typing while allowing other dependencies to bump minor/patch versions safely via `uv lock --upgrade`.
   * [Docs Updated]: Appended ledger record to `.jules/warden.md` validating the memory pipeline corrections.
   * [Release]: v0.1.26 cut, tagged, and ready.

 The head (PR branch) has:
   ## [0.1.26] - 2026-05-12
   * [QA Status]: Verified structural soundness of the circular reference / memory leak fix within DAG evaluation. Core tests pass seamlessly without introducing side effects.
   * [Entropy Pruned]: 0 lines. Codebase zero-bloat state holds intact.
   * [Dependencies Bumped]: Successfully locked `mypy<2` to preserve strict typing while allowing other dependencies to bump minor/patch versions safely via `uv lock --upgrade`.
   * [Docs Updated]: Appended ledger record to `.jules/warden.md` validating the memory pipeline corrections.
   * [Release]: v0.1.26 cut, tagged, and ready.

 They are identical! So we can keep one.

 The base (main) and head (PR branch) have the same content for [0.1.26]. So we just keep one copy.

 Similarly, for [0.1.25], [0.1.24], etc., we see that the base (main) and head (PR branch) have the same content? 

 Let's check [0.1.25]:

 Base (main):
   ## [0.1.25] - 2026-05-07
   * [QA Status]: Verified structural soundness of the `functools.partial` unwrapping optimization. The exact type checking (`type(...) is functools.partial`) was evaluated to safely handle the hot-path execution loop without introducing regressions or breaking fast-fail mechanisms.
   * [Entropy Pruned]: 0 lines. Codebase remains at zero bloat, with FastAPI routing endpoints validated as false positives from `vulture` dead-code scans.
   * [Dependencies Bumped]: Maintained core locked dependencies within `uv.lock`. Successfully rolled back `mypy` update to strictly adhere to `>=1.8.0,<2` constraint to avoid test failures.
   * [Docs Updated]: Documented type checking micro-optimization guidelines in `.jules/warden.md` ledger.
   * [Release]: v0.1.25 cut, tagged, and ready.

 Head (PR branch):
   ## [0.1.25] - 2026-05-07
   * [QA Status]: Verified structural soundness of the `functools.partial` unwrapping optimization. The exact type checking (`type(...) is functools.partial`) was evaluated to safely handle the hot-path execution loop without introducing regressions or breaking fast-fail mechanisms.
   * [Entropy Pruned]: 0 lines. Codebase remains at zero bloat, with FastAPI routing endpoints validated as false positives from `vulture` dead-code scans.
   * [Dependencies Bumped]: Maintained core locked dependencies within `uv.lock`. Successfully rolled back `mypy` update to strictly adhere to `>=1.8.0,<2` constraint to avoid test failures.
   * [Docs Updated]: Documented type checking micro-optimization guidelines in `.jules/warden.md` ledger.
   * [Release]: v0.1.25 cut, tagged, and ready.

 They are identical.

 Similarly, [0.1.24], [0.1.23], [0.1.22], [0.1.21] are identical in both.

 Therefore, we only need to write each version once.

 The plan:

   We will start with the header: "# Changelog" and the description.

   Then we will have:
        ## [0.1.27] - 2026-05-20
        * [Dependencies Bumped]: Safely bumped `certifi` to `v2026.5.20`, `ruff` to `v0.15.14`, and `starlette` to `v1.0.1`.
        * [QA Status]: Verified BOLT's fast-path optimization (`if deps else ()`) for task dependencies during DAG execution to eliminate tuple generator overhead. Passed strict static checks and fail-fast unit tests.
        * [QA Status]: Verified structural soundness of the DAG execution engine optimization. Passing a mutable dictionary of `asyncio.Task` objects to `_run_node` created a memory-leaking reference cycle. The transition to pre-resolved tuples safely breaks this cycle without breaking fail-fast behavior.
        * [Entropy Pruned]: 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
        * [Dependencies Bumped]: Maintained core locked dependencies within `uv.lock`. Updated minor packages securely.
        * [Docs Updated]: Documented memory reference cycle micro-optimization guidelines in `.jules/warden.md` ledger.
        * [Release]: v0.1.27 cut, tagged, and ready.

        ## [0.1.26] - 2026-05-12
        * [QA Status]: Verified structural soundness of the circular reference / memory leak fix within DAG evaluation. Core tests pass seamlessly without introducing side effects.
        * [Entropy Pruned]: 0 lines. Codebase zero-bloat state holds intact.
        * [Dependencies Bumped]: Successfully locked `mypy<2` to preserve strict typing while allowing other dependencies to bump minor/patch versions safely via `uv lock --upgrade`.
        * [Docs Updated]: Appended ledger record to `.jules/warden.md` validating the memory pipeline corrections.
        * [Release]: v0.1.26 cut, tagged, and ready.

        ## [0.1.25] - 2026-05-07
        * [QA Status]: Verified structural soundness of the `functools.partial` unwrapping optimization. The exact type checking (`type(...) is functools.partial`) was evaluated to safely handle the hot-path execution loop without introducing regressions or breaking fast-fail mechanisms.
        * [Entropy Pruned]: 0 lines. Codebase remains at zero bloat, with FastAPI routing endpoints validated as false positives from `vulture` dead-code scans.
        * [Dependencies Bumped]: Maintained core locked dependencies within `uv.lock`. Successfully rolled back `mypy` update to strictly adhere to `>=1.8.0,<2` constraint to avoid test failures.
        * [Docs Updated]: Documented type checking micro-optimization guidelines in `.jules/warden.md` ledger.
        * [Release]: v0.1.25 cut, tagged, and ready.

        ## [0.1.24] - 2026-05-05
        * [QA Status]: Verified structural soundness of the codebase. The fast-fail mechanism correctly utilizes `asyncio.wait` ensuring no unawaited coroutines leak.
        * [QA Status]: Verified structural soundness of the fix for string dependency handling in `WorkflowEngine`. The codebase gracefully handles string inputs as single-element lists without destructing them.
        * [Entropy Pruned]: 0 lines. Scanned for dead code via `vulture`; remaining flags are confirmed as FastAPI/Pydantic false positives. Codebase zero-bloat state holds intact.
        * [Entropy Pruned]: 0 lines. Scanned for dead code via `vulture`; FastAPI router instances flagged are false positives. Codebase zero-bloat state holds intact.
        * [Dependencies Bumped]: Evaluated dependencies via `uv lock --upgrade`. Minor bumps passed perfectly.
        * [Dependencies Bumped]: Maintained locked dependencies at their latest compatible versions.
        * [Docs Updated]: Logged optimization and bugfix details in `warden.md` ledger.
        * [Docs Updated]: Logged optimization and bugfix details in `warden.md` ledger.
        * [Release]: v0.1.24 cut, tagged, and ready.
        * [Release]: v0.1.22 cut, tagged, and ready.   [Wait, note: the base (main) and head (PR branch) both have two [Release] items?]

        But wait, looking at the base (main) context for [0.1.24]:
            * [Release]: v0.1.24 cut, tagged, and ready.
            * [Release]: v0.1.22 cut, tagged, and ready.

        And the head (PR branch) for [0.1.24] has the same.

        However, note that the [0.1.22] release is being logged in the [0.1.24] section? That seems odd.

        But we are to keep all changes, so we keep both.

        Similarly, for [0.1.23]:
            * [Release]: v0.1.23 cut, tagged, and ready.
            * [Release]: v0.1.21 cut, tagged, and ready.

        And for [0.1.22]:
            * [Release]: v0.1.22 cut, tagged, and ready.
            * [Release]: v0.1.20 cut, tagged, and ready.   [But wait, let's check]

        Actually, let's look at the head (PR branch) for [0.1.22]:
            * [Release]: v0.1.22 cut, tagged, and ready.

        And the base (main) for [0.1.22] has:
            * [Release]: v0.1.22 cut, tagged, and ready.
            * [Release]: v0.1.20 cut, tagged, and ready.

        But wait, the base (main) context for [0.1.22] shows:
            * [Release]: v0.1.22 cut, tagged, and ready.
            * [Release]: v0.1.20 cut, tagged, and ready.

        And the head (PR branch) for [0.1.22] shows:
            * [Release]: v0.1.22 cut, tagged, and ready.

        So the base (main) has an extra [Release] item for v0.1.20 in the [0.1.22] section? 

        However, note that the head (PR branch) also has a [0.1.20] section? 

        Let's look at the head (PR branch) context:

            ## [0.1.20] - 2026-04-30
            ... (items)

            ## [0.1.21] - 2026-05-01
            ... (items)

        And then:

            ## [0.1.22] - 2026-05-03
            ... (items)

            * [Release]: v0.1.22 cut, tagged, and ready.

        And the base (main) for [0.1.22] has two [Release] items: one for v0.1.22 and one for v0.1.20.

        This seems like a mistake in the base (main): they put the v0.1.20 release note in the v0.1.22 section.

        But we are to keep all changes. So we will keep both.

        However, note that the head (PR branch) does not have that extra [Release] item for v0.1.20 in the [0.1.22] section. 
        Instead, the head (PR branch) has a separate [0.1.20] section.

        So we must also include the [0.1.20] section from the head (PR branch) and the base (main)? 

        Let's check the base (main) for [0.1.20]: 

        The base (main) context does not show a [0.1.20] section. It shows:

            ## [0.1.22] - 2026-05-03
            ... 
            * [Release]: v0.1.20 cut, tagged, and ready.

        And then it goes to ## [0.1.21] - 2026