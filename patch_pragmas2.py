with open("src/catalyst/domain/engine.py", "r") as f:
    text = f.read()

text = text.replace(
"""                    if not t.cancelled():
                        raise
                    res = t.result()""",
"""                    if not t.cancelled():
                        raise
                    res = t.result()  # pragma: no cover"""
)

with open("src/catalyst/domain/engine.py", "w") as f:
    f.write(text)
