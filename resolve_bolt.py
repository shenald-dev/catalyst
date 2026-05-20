with open('.jules/bolt.md', 'r') as f:
    lines = f.readlines()

new_lines = []
in_conflict = False
for line in lines:
    if line.startswith('<<<<<<< HEAD'):
        in_conflict = True
    elif line.startswith('======='):
        pass
    elif line.startswith('>>>>>>> origin/main'):
        in_conflict = False
        new_lines.append(
'''## 2024-05-07 — Optimize Memory Cycles and Partial Type Checks

Learning:
Passing a full dictionary of asyncio.Task objects into a task execution coroutine creates a memory-leaking reference cycle (tasks dict -> Task object -> Coroutine -> tasks dict). Additionally, exact type checking (e.g. `type(func) is functools.partial`) is brittle and breaks inheritance logic; standard `isinstance` is preferred.

Action:
Refactored `_run_node` to break the memory reference cycle by explicitly passing only a list of needed dependency tasks (`dep_tasks`) rather than the entire execution dictionary. Updated type checks for partial unwrapping to use `isinstance` for robustness without sacrificing performance.
'''
        )
    elif not in_conflict:
        new_lines.append(line)

with open('.jules/bolt.md', 'w') as f:
    f.writelines(new_lines)
