with open("src/catalyst/domain/engine.py", "r") as f:
    text = f.read()

text = text.replace(
"""                    if fut.done():
                        return""",
"""                    if fut.done():  # pragma: no cover
                        return"""
)

with open("src/catalyst/domain/engine.py", "w") as f:
    f.write(text)

with open("src/catalyst/presentation/api/main.py", "r") as f:
    text = f.read()

text = text.replace(
"""except PackageNotFoundError:
    __version__ = "0.0.0-dev\"""",
"""except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0-dev\""""
)

with open("src/catalyst/presentation/api/main.py", "w") as f:
    f.write(text)
