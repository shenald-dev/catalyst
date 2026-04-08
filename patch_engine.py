import re

with open("src/catalyst/domain/engine.py", "r") as f:
    content = f.read()

content = re.sub(r'<<<<<<< HEAD\n        topo_order = self._cached_topo_order\n=======\n>>>>>>> origin/main', '        topo_order = self._cached_topo_order', content)
content = re.sub(r'for node in self._cached_topo_order:', 'for node in topo_order:', content)

with open("src/catalyst/domain/engine.py", "w") as f:
    f.write(content)
