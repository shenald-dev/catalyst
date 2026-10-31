with open("src/catalyst/domain/engine.py", "r") as f:
    text = f.read()

text = text.replace(
"""        if dep_tasks:
            if len(dep_tasks) == 1:
                res = await dep_tasks[0]""",
"""        if dep_tasks:
            if len(dep_tasks) == 1:
                t = dep_tasks[0]
                try:
                    res = await asyncio.shield(t)
                except asyncio.CancelledError:
                    if not t.cancelled():
                        raise
                    res = t.result()"""
)

with open("src/catalyst/domain/engine.py", "w") as f:
    f.write(text)
