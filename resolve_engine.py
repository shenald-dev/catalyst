with open('src/catalyst/domain/engine.py', 'r') as f:
    lines = f.readlines()

new_lines = []
in_conflict_1 = False
in_conflict_2 = False
for line in lines:
    if line.startswith('<<<<<<< HEAD'):
        if 'dep_tasks:' in lines[lines.index(line)+1]:
            in_conflict_1 = True
        else:
            in_conflict_2 = True
    elif line.startswith('======='):
        pass
    elif line.startswith('>>>>>>> origin/main'):
        if in_conflict_1:
            in_conflict_1 = False
            new_lines.append('        dep_tasks: tuple[asyncio.Task[Any], ...],\n')
        elif in_conflict_2:
            in_conflict_2 = False
            new_lines.append('            deps = self._predecessors.get(node, [])\n')
            new_lines.append('            dep_tasks = tuple(tasks[dep] for dep in deps)\n')
    elif not in_conflict_1 and not in_conflict_2:
        new_lines.append(line)

with open('src/catalyst/domain/engine.py', 'w') as f:
    f.writelines(new_lines)
