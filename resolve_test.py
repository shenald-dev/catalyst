with open('tests/test_fail_fast.py', 'r') as f:
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
        new_lines.append('    async def wrapped_run_node(node: str, dep_tasks: Tuple[asyncio.Task[Any], ...]) -> Any:\n')
    elif not in_conflict:
        new_lines.append(line)

with open('tests/test_fail_fast.py', 'w') as f:
    f.writelines(new_lines)
