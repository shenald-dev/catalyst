"""
Enhanced DAG (Directed Acyclic Graph) for workflow orchestration.

Provides:
- Graph construction and validation
- Topological sorting into executable layers
- DOT export for visualization
- Query methods (roots, leaves, critical path)
- Cycle detection with informative errors
"""

from collections import defaultdict, deque
from typing import Dict, Set, List, Optional
from dataclasses import dataclass, field


class DAGError(Exception):
    """Base exception for DAG errors."""
    pass


class CyclicDependencyError(DAGError):
    """Raised when a cycle is detected in the DAG."""
    pass


class MissingDependencyError(DAGError):
    """Raised when a task depends on an unknown task."""
    pass


@dataclass
class TaskNode:
    """Represents a node in the DAG."""
    name: str
    dependencies: Set[str] = field(default_factory=set)  # immediate predecessors (parents)
    dependents: Set[str] = field(default_factory=set)    # immediate successors (children)
    metadata: Dict = field(default_factory=dict)         # arbitrary metadata (duration, priority, etc.)

    def __post_init__(self):
        if not isinstance(self.dependencies, set):
            self.dependencies = set(self.dependencies)
        if not isinstance(self.dependents, set):
            self.dependents = set(self.dependents)


class DAG:
    """
    Directed Acyclic Graph for managing task dependencies.

    Usage:
        dag = DAG()
        dag.add_task("build")
        dag.add_task("test", dependencies={"build"})
        dag.add_task("deploy", dependencies={"test"})
        layers = dag.topological_sort()
        dot = dag.export_dot()
    """

    def __init__(self):
        self._nodes: Dict[str, TaskNode] = {}

    def add_task(self, name: str, dependencies: Optional[Set[str]] = None, **metadata):
        """
        Add a task to the DAG.

        Args:
            name: Unique task identifier
            dependencies: Set of task names that must complete before this task
            **metadata: Additional data (duration, priority, etc.)
        """
        if name in self._nodes:
            raise ValueError(f"Task '{name}' already exists in DAG")

        deps = set(dependencies) if dependencies else set()
        node = TaskNode(name=name, dependencies=deps, metadata=metadata)
        self._nodes[name] = node

        # For each existing dependency, add this node to that dependency's dependents
        for dep in deps:
            if dep in self._nodes:
                self._nodes[dep].dependents.add(name)

        # For each existing node that depends on this new node, add that node to this node's dependents
        for other_name, other_node in list(self._nodes.items()):
            if other_name == name:
                continue
            if name in other_node.dependencies:
                node.dependents.add(other_name)

    def remove_task(self, name: str):
        """Remove a task and its edges from the DAG."""
        if name not in self._nodes:
            return
        node = self._nodes[name]
        # Remove from dependents of dependencies
        for dep in node.dependencies:
            if dep in self._nodes:
                self._nodes[dep].dependents.discard(name)
        # Remove dependents' reference to this node
        for dep_name in node.dependents:
            if dep_name in self._nodes:
                self._nodes[dep_name].dependencies.discard(name)
        del self._nodes[name]

    def validate(self) -> None:
        """
        Validate the DAG structure.

        Checks:
        - All dependencies reference existing tasks
        - No cycles exist

        Raises:
            MissingDependencyError: If a dependency is missing
            CyclicDependencyError: If a cycle is detected
        """
        # Check for missing dependencies
        for name, node in self._nodes.items():
            for dep in node.dependencies:
                if dep not in self._nodes:
                    raise MissingDependencyError(
                        f"Task '{name}' depends on unknown task '{dep}'"
                    )

        # Detect cycles using DFS with parent tracking
        visited = set()
        rec_stack = set()
        parent: Dict[str, str] = {}  # child -> parent in DFS tree

        def dfs(u: str) -> bool:
            visited.add(u)
            rec_stack.add(u)
            for v in self._nodes[u].dependents:
                if v not in visited:
                    parent[v] = u
                    if not dfs(v):
                        return False
                elif v in rec_stack:
                    # Found cycle: reconstruct path from v to u then back to v
                    cycle = self._reconstruct_cycle(parent, u, v)
                    raise CyclicDependencyError(
                        f"Cyclic dependency detected: {' -> '.join(cycle)}"
                    )
            rec_stack.remove(u)
            return True

        for node_name in self._nodes:
            if node_name not in visited:
                parent.clear()
                parent[node_name] = None  # root marker
                if not dfs(node_name):
                    return False
        return True

    def _reconstruct_cycle(self, parent: Dict[str, str], u: str, v: str) -> List[str]:
        """
        Reconstruct a cycle given a back edge u -> v where v is in the recursion stack.
        Returns a list representing the cycle: v -> ... -> u -> v.
        """
        # Build path from u back to v using parent map
        path = [u]
        cur = u
        while cur in parent and parent[cur] is not None and cur != v:
            cur = parent[cur]
            path.append(cur)
        if cur != v:
            # Could not reconstruct fully; fallback to simple edge
            path.append(v)
        else:
            path.append(v)
        path.reverse()
        return path

    def topological_sort(self) -> List[List[str]]:
        """
        Sort tasks into layers of parallel execution.

        Returns:
            List of layers, where each layer is a list of task names that can run concurrently.
        """
        self.validate()  # ensure consistent

        # Compute in-degree (number of dependencies) for each node
        in_degree: Dict[str, int] = {name: 0 for name in self._nodes}
        for node in self._nodes.values():
            in_degree[node.name] = len(node.dependencies)

        # Start with tasks having zero in-degree (roots)
        queue = deque([name for name, deg in in_degree.items() if deg == 0])
        layers: List[List[str]] = []

        while queue:
            current_layer = []
            for _ in range(len(queue)):
                u = queue.popleft()
                current_layer.append(u)
                for v in self._nodes[u].dependents:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        queue.append(v)
            layers.append(current_layer)

        # Verify all tasks were included
        total_tasks = sum(len(layer) for layer in layers)
        if total_tasks != len(self._nodes):
            # Should not happen if validate passed, but defensive
            raise CyclicDependencyError(
                f"Cycle detected during sort: {total_tasks} tasks placed out of {len(self._nodes)}"
            )

        return layers

    def export_dot(self, rankdir: str = "TB") -> str:
        """
        Export DAG as Graphviz DOT format.

        Args:
            rankdir: Graph direction (TB, LR, RL, BT)

        Returns:
            DOT string
        """
        lines = [
            "digraph G {",
            f"    rankdir={rankdir};",
            "    node [shape=box, style=rounded, fontname=Helvetica];"
        ]
        for name in self._nodes:
            lines.append(f'    "{name}";')
        for name, node in self._nodes.items():
            for dep in node.dependencies:
                lines.append(f'    "{dep}" -> "{name}";')
        lines.append("}")
        return "\n".join(lines)

    def roots(self) -> Set[str]:
        """Tasks with no dependencies."""
        return {name for name, node in self._nodes.items() if not node.dependencies}

    def leaves(self) -> Set[str]:
        """Tasks with no dependents."""
        return {name for name, node in self._nodes.items() if not node.dependents}

    def critical_path(self) -> List[str]:
        """
        Compute the critical path (longest duration path) through the DAG.

        Requires each task to have 'duration' in metadata (float in seconds).
        If duration is missing, defaults to 1.0 to treat each task as unit weight.
        """
        # Get a valid topological order (use our already validated DAG)
        order = []
        in_degree = {name: 0 for name in self._nodes}
        for node in self._nodes.values():
            in_degree[node.name] = len(node.dependencies)
        queue = deque([n for n, d in in_degree.items() if d == 0])
        while queue:
            u = queue.popleft()
            order.append(u)
            for v in self._nodes[u].dependents:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # Longest path DP: dist[node] = longest duration to reach node (including node's duration)
        dist: Dict[str, float] = {}
        pred: Dict[str, str] = {}

        for name in order:
            dur = self._nodes[name].metadata.get('duration', 1.0)
            if not self._nodes[name].dependencies:
                dist[name] = dur
                pred[name] = None
            else:
                # Find predecessor with maximum distance
                max_pred = None
                max_val = -1.0
                for dep in self._nodes[name].dependencies:
                    if dep not in dist:
                        continue  # Should not happen in a valid topological order
                    val = dist[dep]
                    if val > max_val:
                        max_val = val
                        max_pred = dep
                if max_pred is not None:
                    dist[name] = dist[max_pred] + dur
                    pred[name] = max_pred
                else:
                    # No predecessor had distance? Shouldn't happen; treat as start
                    dist[name] = dur
                    pred[name] = None

        if not dist:
            return []

        # Sink node: node with maximum distance
        sink = max(dist, key=dist.get)
        # Reconstruct path from sink to source
        path = []
        cur = sink
        while cur is not None:
            path.append(cur)
            cur = pred.get(cur)
        path.reverse()
        return path

    def size(self) -> int:
        """Number of tasks in the DAG."""
        return len(self._nodes)

    def get_task(self, name: str) -> TaskNode:
        """Retrieve a task node."""
        return self._nodes[name]

    def __iter__(self):
        return iter(self._nodes.values())

    def __len__(self):
        return len(self._nodes)
