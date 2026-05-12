with open("src/catalyst/domain/engine.py", "r") as f:
    content = f.read()

# Replace block 1
content = content.replace("""<<<<<<< HEAD
        dependency_tasks: list[asyncio.Task[Any]],
=======
        dep_tasks: tuple[asyncio.Task[Any], ...],
>>>>>>> origin/main""", """        dep_tasks: tuple[asyncio.Task[Any], ...],""")

# Replace block 2
content = content.replace("""<<<<<<< HEAD
        if dependency_tasks:
            if len(dependency_tasks) == 1:
                res = await dependency_tasks[0]
=======
        if dep_tasks:
            if len(dep_tasks) == 1:
                res = await dep_tasks[0]
>>>>>>> origin/main""", """        if dep_tasks:
            if len(dep_tasks) == 1:
                res = await dep_tasks[0]""")

# Replace block 3
content = content.replace("""<<<<<<< HEAD
                pending_set = set(dependency_tasks)
=======
                pending_set = set(dep_tasks)
>>>>>>> origin/main""", """                pending_set = set(dep_tasks)""")

# Replace block 4
content = content.replace("""<<<<<<< HEAD
            dep_tasks = [tasks[dep] for dep in self._predecessors.get(node, [])]
=======
            deps = self._predecessors.get(node, [])
            dep_tasks = tuple(tasks[dep] for dep in deps)
>>>>>>> origin/main""", """            deps = self._predecessors.get(node, [])
            dep_tasks = tuple(tasks[dep] for dep in deps)""")

with open("src/catalyst/domain/engine.py", "w") as f:
    f.write(content)
