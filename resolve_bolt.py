with open(".jules/bolt.md", "r") as f:
    content = f.read()

import re
resolved = re.sub(
r"<<<<<<< HEAD.*?=======\n(.*?)>>>>>>> origin/jules-warden-v0.1.25-9917569268494397081",
r"\1",
content, flags=re.DOTALL
)

with open(".jules/bolt.md", "w") as f:
    f.write(resolved)
