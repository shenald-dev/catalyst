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

    # Phase 2: Enhanced task configuration
    resources: Dict[str, float] = field(default_factory=dict)  # resource requirements (cpu, memory_mb, io_weight)
    timeout: Optional[float] = None  # timeout in seconds, None = no timeout
    retry_policy: Dict = field(default_factory=dict)  # retry config: max_attempts, backoff_factor, retry_on

    metadata: Dict = field(default_factory=dict)  # arbitrary additional metadata

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

    def add_task(self, name: str, dependencies: Optional[Set[str]] = None,
                 resources: Optional[Dict[str, float]] = None,
                 timeout: Optional[float] = None,
                 retry_policy: Optional[Dict] = None,
                 **metadata):
        """
        Add a task to the DAG.

        Args:
            name: Unique task identifier
            dependencies: Set of task names that must complete before this task
            resources: Resource requirements (e.g., {"cpu": 1.0, "memory_mb": 512})
            timeout: Timeout in seconds (None = no timeout)
            retry_policy: Retry configuration (e.g., {"max_attempts": 3, "backoff_factor": 2.0})
            **metadata: Additional arbitrary data (duration, priority, etc.)
        """
        if name in self._nodes:
            raise ValueError(f"Task '{name}' already exists in DAG")

        deps = set(dependencies) if dependencies else set()
        node = TaskNode(
            name=name,
            dependencies=deps,
            resources=resources or {},
            timeout=timeout,
            retry_policy=retry_policy or {},
            metadata=metadata
        )
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

        # Detect cycles using iterative DFS with parent tracking (avoid recursion limits)
        # State: 0=unvisited, 1=visiting (in stack), 2=visited
        state: Dict[str, int] = {name: 0 for name in self._nodes}
        parent: Dict[str, str] = {}

        for start_node in self._nodes:
            if state[start_node] != 0:
                continue
            # Initialize DFS from this node
            state[start_node] = 1
            parent[start_node] = None
            stack = [(start_node, iter(self._nodes[start_node].dependents))]

            while stack:
                current, neighbors_iter = stack[-1]
                try:
                    neighbor = next(neighbors_iter)
                    if state[neighbor] == 0:
                        # Visit neighbor
                        state[neighbor] = 1
                        parent[neighbor] = current
                        stack.append((neighbor, iter(self._nodes[neighbor].dependents)))
                    elif state[neighbor] == 1:
                        # Cycle detected: neighbor is in current DFS path
                        cycle = self._reconstruct_cycle(parent, current, neighbor)
                        raise CyclicDependencyError(
                            f"Cyclic dependency detected: {' -> '.join(cycle)}"
                        )
                    # else state[neighbor] == 2: already fully visited, ignore
                except StopIteration:
                    # All neighbors processed
                    state[current] = 2
                    stack.pop()

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

    def estimated_makespan(self, resource_limits: Optional[Dict[str, float]] = None) -> float:
        """
        Estimate the total execution time of the DAG.

        Two modes:
        1. Unlimited resources (default): returns the length of the critical path.
        2. Resource-constrained (provide `resource_limits`): simulates list scheduling
           to approximate makespan given limited resources.

        Args:
            resource_limits: Dict of available resources (e.g., {"cpu": 4.0, "memory_mb": 8192}).
                If None or empty, uses unlimited-resources estimate (critical path sum).

        Returns:
            Estimated makespan in seconds.

        Note:
            Resource-aware estimation assumes:
            - Tasks have 'duration' in metadata (default 1.0).
            - Task resource requirements are in `TaskNode.resources`.
            - Scheduling policy: a task can start when:
                * All dependencies are finished
                * Required resources are simultaneously available.
            This is a heuristic (list scheduling) and may overestimate optimal makespan.
        """
        # Unlimited resources: fast path (existing behavior)
        if not resource_limits:
            path = self.critical_path()
            if not path:
                return 0.0
            total = 0.0
            for name in path:
                node = self._nodes[name]
                total += node.metadata.get('duration', 1.0)
            return total

        # Resource-constrained estimation via list scheduling simulation
        import heapq

        # Get topological order
        try:
            order = self.topological_sort()
        except (CyclicDependencyError, MissingDependencyError):
            # Should not happen if validate passed, but be safe
            return 0.0

        # Flatten layers into a single order respecting dependencies
        # We'll compute nodes in topological order by in-degree processing
        # Build explicit topological order using Kahn's algorithm
        in_degree = {name: 0 for name in self._nodes}
        for node in self._nodes.values():
            for dep in node.dependencies:
                in_degree[dep] = 1 if dep in in_degree else in_degree[dep] + 1  # not used; actually we need reverse mapping; but simpler: recalc from nodes:
        # Actually recompute properly:
        in_degree = {name: 0 for name in self._nodes}
        for node in self._nodes.values():
            for dep in node.dependencies:
                in_degree[dep] = in_degree.get(dep, 0) + 1  # but dep is in _nodes, so:
        # Let's do it correctly:
        in_degree = {name: 0 for name in self._nodes}
        for node in self._nodes.values():
            for dep in node.dependencies:
                in_degree[dep] = in_degree.get(dep, 0) + 1
        # Actually better: count indegree from dependencies:
        in_degree = {name: 0 for name in self._nodes}
        for name, node in self._nodes.items():
            for dep in node.dependencies:
                if dep in in_degree:
                    in_degree[dep] += 1
                else:
                    in_degree[dep] = 1
        # Wait, that's the reverse: indegree of node = number of dependencies? Actually indegree = number of incoming edges = number of dependencies? In DAG, each dependency edge goes from dep->node, so indegree of node = len(dependencies). So simpler:
        in_degree = {name: len(node.dependencies) for name, node in self._nodes.items()}

        # Kahn's algorithm to get a linear topo order
        topo_order: List[str] = []
        queue = deque([n for n, d in in_degree.items() if d == 0])
        while queue:
            u = queue.popleft()
            topo_order.append(u)
            for v in self._nodes[u].dependents:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # Precompute earliest possible start ignoring resources (just deps)
        earliest_start: Dict[str, float] = {}
        for name in topo_order:
            node = self._nodes[name]
            duration = node.metadata.get('duration', 1.0)
            if not node.dependencies:
                earliest_start[name] = 0.0
            else:
                # max of (earliest_start[dep] + duration[dep])
                max_completion = 0.0
                for dep in node.dependencies:
                    dep_finish = earliest_start.get(dep, 0.0) + self._nodes[dep].metadata.get('duration', 1.0)
                    if dep_finish > max_completion:
                        max_completion = dep_finish
                earliest_start[name] = max_completion

        # List scheduling simulation
        # Maintain current allocated resources per resource type (accumulated)
        allocated: Dict[str, float] = {res: 0.0 for res in resource_limits}
        # Event heap: (release_time, resource_type, amount)
        events: List[tuple] = []  # (release_time, resource, amount)
        # We'll assign tasks greedily when they become eligible and resources are available
        # Track when each task actually starts and finishes
        start_time: Dict[str, float] = {}
        finish_time: Dict[str, float] = {}

        # We'll iterate through tasks in topological order, but actual scheduling may delay
        # We need to consider that a task can only start after all deps finish AND resources are free.
        # We'll simulate time by processing events (task completions that free resources) and trying to schedule pending tasks.
        # Instead of a full discrete event simulation, we can use a simpler approach:
        # For each task in topo order, compute its actual start time as the maximum of:
        #   - earliest_start[task] (all deps done)
        #   - earliest time when needed resources become available (accounting for currently allocated resources)
        # We need to know resource allocation timeline. We can iterate tasks and adjust for contention within the same critical path.
        # But tasks can run in parallel, and their durations overlap. Harder to compute analytically.
        # So we'll do a simple greedy simulation:
        # Keep a set of tasks that are ready (deps satisfied). Initially tasks with indegree 0.
        # Track current time, current allocated resources.
        # At each step, if we have resources to run any ready task, schedule it; else, fast-forward to next resource release event.
        #
        # Represent ready tasks as a list (or priority by duration? doesn't matter for makespan). We'll just schedule as possible.
        #
        # Let's implement discrete-event style:
        # - Current time
        # - Ready tasks (set or list)
        # - Running tasks (track finish times and resource allocations)
        # - While tasks remain to be scheduled:
        #   - Check if any running tasks finish at current time; release resources.
        #   - Add newly eligible tasks ( whose dependencies just completed )
        #   - While resources can accommodate any ready task, schedule it (assign start/finish, allocate resources, add to running)
        #   - If no ready task can be scheduled and there are still tasks, advance time to next event (earliest finish of running tasks)
        #
        # But we only need makespan (last finish time). So simpler: approximate by simulating resource contention in topological order without full event loop might not be accurate for complex DAGs. We'll go for event loop for accuracy.

        # Rebuild adjacency
        dependencies = {name: set(node.dependencies) for name, node in self._nodes.items()}
        dependents = {name: set(node.dependents) for name, node in self._nodes.items()}
        durations = {name: node.metadata.get('duration', 1.0) for name, node in self._nodes.items()}
        task_resources = {name: node.resources or {} for name, node in self._nodes.items()}

        # State
        remaining_deps = {name: len(self._nodes[name].dependencies) for name in self._nodes}
        ready = deque([n for n, r in remaining_deps.items() if r == 0])
        # Remove ready tasks from remaining_deps? We'll decrement as deps finish.
        # Running tasks: heap of (finish_time, task_name)
        running: List[tuple] = []
        # Resource allocation tracking per resource type (total allocated)
        allocated = {res: 0.0 for res in resource_limits}
        current_time = 0.0
        makespan = 0.0
        # Number of tasks still to complete
        tasks_left = len(self._nodes)

        # We'll process events: task completions release resources and may make new tasks ready
        while tasks_left > 0:
            # If any running tasks finish at or before current_time, complete them
            while running and running[0][0] <= current_time:
                finish, finished_task = heapq.heappop(running)
                # Release resources
                for res, amt in task_resources[finished_task].items():
                    if res in allocated:
                        allocated[res] -= amt
                        if allocated[res] < 0:
                            allocated[res] = 0.0
                tasks_left -= 1
                makespan = max(makespan, finish)
                # For each dependent of finished_task, decrement remaining_deps; if becomes 0, add to ready
                for child in dependents[finished_task]:
                    remaining_deps[child] -= 1
                    if remaining_deps[child] == 0:
                        ready.append(child)

            # Try to schedule as many ready tasks as possible respecting resource limits
            # We'll iterate over a snapshot of ready list; schedule if resources enough.
            newly_scheduled = 0
            # Using list to allow popping while iterating? We'll use a queue and process in order.
            ready_len = len(ready)
            for _ in range(ready_len):
                task = ready.popleft()
                # Check if resources can accommodate
                can_schedule = True
                for res, amt in task_resources[task].items():
                    # Only enforce limits for resources that are defined in resource_limits.
                    if res in resource_limits:
                        if allocated[res] + amt > resource_limits[res]:
                            can_schedule = False
                            break
                if can_schedule:
                    # Allocate resources
                    for res, amt in task_resources[task].items():
                        allocated[res] += amt
                    # Compute start time = current_time (since deps satisfied and resources now allocated)
                    start_time[task] = current_time
                    finish = current_time + durations[task]
                    finish_time[task] = finish
                    heapq.heappush(running, (finish, task))
                    newly_scheduled += 1
                else:
                    # Not enough resources now; put back at end of ready queue to try later after some release
                    ready.append(task)
            # If we couldn't schedule any ready tasks (or there were none), we must wait for next resource release
            if newly_scheduled == 0 and tasks_left > 0:
                if running:
                    # Advance current_time to earliest finish
                    current_time = running[0][0]
                else:
                    # No running tasks but still tasks left? Shouldn't happen unless deadlock due to missing resources
                    # But if no running tasks, we can't make progress; but ready shouldn't be empty if tasks remain and DAG connected...
                    # Break to avoid infinite loop
                    # In case of resource deadlock (all ready tasks need resources that are allocated and never freed due to circular dependency?), this could hang.
                    # We'll assume DAG acyclic and resources finite but not deadlocked.
                    # But if ready is empty and running not empty, we'll just wait.
                    # if ready empty and running empty but tasks_left>0 => disconnected DAGs? Actually all remaining tasks may have unsatisfied deps due to missing resources from future tasks? That's impossible. So we can assert.
                    break

        return makespan if makespan > 0 else 0.0

    def is_reachable(self, from_task: str, to_task: str) -> bool:
        """
        Check if there is a directed path from `from_task` to `to_task`.

        Args:
            from_task: Starting task name
            to_task: Target task name

        Returns:
            True if reachable, False otherwise.

        Note:
            Uses iterative DFS; safe for large DAGs modulo stack depth.
        """
        if from_task not in self._nodes or to_task not in self._nodes:
            return False
        if from_task == to_task:
            return True
        stack = [from_task]
        visited = set()
        while stack:
            current = stack.pop()
            if current == to_task:
                return True
            if current in visited:
                continue
            visited.add(current)
            node = self._nodes[current]
            for child in node.dependents:
                if child not in visited:
                    stack.append(child)
        return False

    def get_ancestors(self, task_name: str) -> Set[str]:
        """
        Return the set of all tasks that are direct or indirect dependencies of `task_name`.

        Args:
            task_name: The task whose ancestors to retrieve.

        Returns:
            Set of ancestor task names. Empty if task has no dependencies.

        Raises:
            KeyError: If the task does not exist.
        """
        if task_name not in self._nodes:
            raise KeyError(f"Task '{task_name}' not found")
        ancestors = set()
        stack = [task_name]
        visited = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            node = self._nodes[current]
            for dep in node.dependencies:
                if dep not in ancestors:
                    ancestors.add(dep)
                    stack.append(dep)
        return ancestors

    def get_descendants(self, task_name: str) -> Set[str]:
        """
        Return the set of all tasks that directly or indirectly depend on `task_name`.

        Args:
            task_name: The task whose descendants to retrieve.

        Returns:
            Set of descendant task names. Empty if task has no dependents.

        Raises:
            KeyError: If the task does not exist.
        """
        if task_name not in self._nodes:
            raise KeyError(f"Task '{task_name}' not found")
        descendants = set()
        stack = [task_name]
        visited = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            node = self._nodes[current]
            for child in node.dependents:
                if child not in descendants:
                    descendants.add(child)
                    stack.append(child)
        return descendants

    def get_depth(self, task_name: str) -> int:
        """
        Return the maximum number of edges from any root to `task_name`.

        Roots (tasks with no dependencies) have depth 0.
        If the DAG is not fully connected and the task is not reachable from any root, returns 0.

        Args:
            task_name: The task to compute depth for.

        Returns:
            Integer depth (>= 0).

        Raises:
            KeyError: If the task does not exist.
        """
        if task_name not in self._nodes:
            raise KeyError(f"Task '{task_name}' not found")
        # Compute depths via topological order
        order = self.topological_sort()
        depths: Dict[str, int] = {}
        for layer in order:
            for name in layer:
                node = self._nodes[name]
                if not node.dependencies:
                    depths[name] = 0
                else:
                    # take max depth of dependencies
                    max_parent = max(depths[dep] for dep in node.dependencies)
                    depths[name] = max_parent + 1
        return depths.get(task_name, 0)

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

    # --- Serialization (msgspec-accelerated) ---
    def to_dict(self) -> dict:
        """Serialize DAG to a plain Python dict (for JSON/msgpack)."""
        return {
            "nodes": {
                name: {
                    "dependencies": list(node.dependencies),
                    "dependents": list(node.dependents),
                    "resources": node.resources,
                    "timeout": node.timeout,
                    "retry_policy": node.retry_policy,
                    "metadata": node.metadata,
                }
                for name, node in self._nodes.items()
            }
        }

    def from_dict(self, data: dict) -> None:
        """Deserialize DAG from a dict (as produced by to_dict)."""
        self._nodes.clear()
        nodes_data = data.get("nodes", {})
        for name, nd in nodes_data.items():
            node = TaskNode(
                name=name,
                dependencies=set(nd.get("dependencies", [])),
                dependents=set(nd.get("dependents", [])),
                resources=nd.get("resources", {}),
                timeout=nd.get("timeout"),
                retry_policy=nd.get("retry_policy", {}),
                metadata=nd.get("metadata", {}),
            )
            self._nodes[name] = node

    def serialize(self) -> bytes:
        """
        Serialize DAG to bytes using msgpack (msgspec) if available,
        otherwise JSON. Returns bytes.
        """
        data = self.to_dict()
        try:
            import msgspec
            return msgspec.msgpack.encode(data)
        except ImportError:
            import json
            return json.dumps(data).encode('utf-8')

    @classmethod
    def deserialize(cls, blob: bytes) -> 'DAG':
        """
        Deserialize DAG from bytes produced by serialize().
        """
        dag = cls()
        try:
            import msgspec
            data = msgspec.msgpack.decode(blob)
        except ImportError:
            import json
            data = json.loads(blob.decode('utf-8'))
        dag.from_dict(data)
        return dag
