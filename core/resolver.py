"""
Catalyst Lab: DAG (Directed Acyclic Graph) Resolver.
"""
from collections import deque
from typing import List, Dict, Set

class DependencyError(Exception):
    pass

class DAGResolver:
    @staticmethod
    def resolve(tasks: List[Dict]) -> List[List[str]]:
        """
        Resolves task dependencies and returns a list of execution layers.
        Each layer contains task names that can be run in parallel.
        """
        graph: Dict[str, Set[str]] = {t["name"]: set(t.get("depends_on", [])) for t in tasks}
        in_degree: Dict[str, int] = {name: 0 for name in graph}
        
        # Calculate in-degrees
        for name in graph:
            for dep in graph[name]:
                if dep not in graph:
                    raise DependencyError(f"Task '{name}' depends on unknown task '{dep}'")
                # We want the reverse to find what follows what
                pass 
        
        # Proper adjacency list for topological sort
        adj: Dict[str, List[str]] = {name: [] for name in graph}
        for name, deps in graph.items():
            for dep in deps:
                adj[dep].append(name)
                in_degree[name] += 1

        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        layers = []

        while queue:
            current_layer = []
            for _ in range(len(queue)):
                u = queue.popleft()
                current_layer.append(u)
                for v in adj[u]:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        queue.append(v)
            layers.append(current_layer)

        if sum(len(layer) for layer in layers) != len(graph):
            raise DependencyError("Circular dependency detected in task graph.")

        return layers

if __name__ == "__main__":
    # Test cases
    test_tasks = [
        {"name": "build", "depends_on": []},
        {"name": "test", "depends_on": ["build"]},
        {"name": "lint", "depends_on": ["build"]},
        {"name": "deploy", "depends_on": ["test", "lint"]},
        {"name": "notify", "depends_on": ["deploy"]}
    ]
    
    resolver = DAGResolver()
    try:
        execution_plan = resolver.resolve(test_tasks)
        print("[SUCCESS] Dependency Resolution")
        for i, layer in enumerate(execution_plan):
            print(f"Layer {i+1}: {layer}")
    except Exception as e:
        print(f"[ERROR] {e}")
