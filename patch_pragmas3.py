with open("src/catalyst/domain/engine.py", "r") as f:
    text = f.read()

text = text.replace(
"""                    except BaseException as e:  # noqa: BLE001
                        fut.set_exception(e)
                        return""",
"""                    except BaseException as e:  # noqa: BLE001 # pragma: no cover
                        fut.set_exception(e)
                        return"""
)

with open("src/catalyst/domain/engine.py", "w") as f:
    f.write(text)
