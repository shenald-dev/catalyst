with open(".jules/bolt.md", "r") as f:
    content = f.read()

import re
# Simply remove the conflict markers
content = content.replace("<<<<<<< HEAD\n", "")
content = content.replace("=======\n", "")
content = content.replace(">>>>>>> origin/main\n", "")

with open(".jules/bolt.md", "w") as f:
    f.write(content)
