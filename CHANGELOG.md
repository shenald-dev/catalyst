We are given a merge conflict in a markdown file (CHANGELOG.md) with three versions: ancestor, base (main), and head (PR branch).
 The goal is to perform a 3-way merge, keeping all meaningful changes from both branches.

 Steps:
 1. We note that the base (main) has a version [0.1.28] (from the base file content) and the head (PR) branch has [0.1.26] (from the head file content?).
    However, looking at the provided diff (Head changes vs base) we see that