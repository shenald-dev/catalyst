"""Unit tests for Catalyst DAG implementation."""
import pytest
from core.dag import DAG, TaskNode, CyclicDependencyError, MissingDependencyError


class TestDAGConstruction:
    """Test DAG node addition and graph building."""

    def test_add_single_task(self):
        dag = DAG()
        dag.add_task("A")
        assert dag.size() == 1
        assert "A" in list(dag._nodes)

    def test_add_multiple_tasks(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B")
        dag.add_task("C")
        assert dag.size() == 3

    def test_add_task_with_dependencies(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"B"})
        node_b = dag.get_task("B")
        assert "A" in node_b.dependencies
        node_a = dag.get_task("A")
        assert "B" in node_a.dependents

    def test_duplicate_task_raises(self):
        dag = DAG()
        dag.add_task("A")
        with pytest.raises(ValueError):
            dag.add_task("A")

    def test_missing_dependency_raises(self):
        dag = DAG()
        dag.add_task("A")
        # Should raise when adding B with dependency on non-existent C
        with pytest.raises(MissingDependencyError):
            dag.add_task("B", dependencies={"non_existent"})

    def test_remove_task_cleans_edges(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.remove_task("A")
        assert "A" not in dag._nodes
        node_b = dag.get_task("B")
        assert "A" not in node_b.dependencies


class TestDAGValidation:
    """Test DAG structure validation."""

    def test_simple_acyclic_validates(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"A", "B"})
        # Should not raise
        dag.validate()

    def test_self_dependency_cycle(self):
        dag = DAG()
        dag.add_task("A", dependencies={"A"})
        with pytest.raises(CyclicDependencyError):
            dag.validate()

    def test_two_node_cycle(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        # Add edge back to create cycle, but we need to modify dependencies directly
        # since DAG.add_task only adds forward edges. We'll manually create the cycle:
        dag._nodes["A"].dependencies.add("B")
        dag._nodes["B"].dependents.add("A")
        with pytest.raises(CyclicDependencyError):
            dag.validate()

    def test_complex_cycle(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"B"})
        dag.add_task("D", dependencies={"C", "A"})
        # Introduce a cycle: D -> A -> B -> C -> D? Actually let's do A->B->C->A
        dag._nodes["A"].dependencies.add("C")
        dag._nodes["C"].dependents.add("A")
        with pytest.raises(CyclicDependencyError):
            dag.validate()


class TestTopologicalSort:
    """Test layer-based topological sorting."""

    def test_linear_dag(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"B"})
        layers = dag.topological_sort()
        assert layers == [["A"], ["B"], ["C"]]

    def test_branching_dag(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"A"})
        dag.add_task("D", dependencies={"B", "C"})
        layers = dag.topological_sort()
        # Layer 0: A; Layer 1: B, C (order may vary); Layer 2: D
        assert set(layers[0]) == {"A"}
        assert set(layers[1]) == {"B", "C"}
        assert layers[2] == ["D"]

    def test_diamond_dag(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"A"})
        dag.add_task("D", dependencies={"B", "C"})
        layers = dag.topological_sort()
        assert len(layers) == 3
        assert layers[0] == ["A"]
        assert set(layers[1]) == {"B", "C"}
        assert layers[2] == ["D"]


class TestDAGQueries:
    """Test DAG query methods."""

    def test_roots(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"A"})
        roots = dag.roots()
        assert roots == {"A"}

    def test_leaves(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"A"})
        leaves = dag.leaves()
        assert leaves == {"B", "C"}

    def test_critical_path_simple(self):
        dag = DAG()
        dag.add_task("A", metadata={"duration": 2.0})
        dag.add_task("B", dependencies={"A"}, metadata={"duration": 3.0})
        dag.add_task("C", dependencies={"A"}, metadata={"duration": 1.0})
        dag.add_task("D", dependencies={"B", "C"}, metadata={"duration": 1.0})
        path = dag.critical_path()
        # Critical path should be A -> B -> D (2+3+1 = 6) vs A->C->D (2+1+1=4)
        assert path == ["A", "B", "D"]

    def test_critical_path_with_equal_durations(self):
        dag = DAG()
        dag.add_task("A", metadata={"duration": 1.0})
        dag.add_task("B", dependencies={"A"}, metadata={"duration": 1.0})
        dag.add_task("C", dependencies={"A"}, metadata={"duration": 1.0})
        dag.add_task("D", dependencies={"B", "C"}, metadata={"duration": 1.0})
        path = dag.critical_path()
        # Either path is valid; we expect length 3
        assert len(path) == 3
        assert path[0] == "A"
        assert "D" in path

    def test_critical_path_missing_durations_defaults(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dag.add_task("C", dependencies={"B"})
        # No durations provided; default 1.0 each
        path = dag.critical_path()
        assert path == ["A", "B", "C"]


class TestDAGExport:
    """Test DOT export."""

    def test_export_dot_simple(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dot = dag.export_dot()
        assert "digraph G" in dot
        assert '"A" -> "B";' in dot
        assert '"A";' in dot
        assert '"B";' in dot

    def test_export_dot_rankdir(self):
        dag = DAG()
        dag.add_task("A")
        dag.add_task("B", dependencies={"A"})
        dot = dag.export_dot(rankdir="LR")
        assert 'rankdir=LR' in dot
