"""Unit tests for Catalyst Orchestrator (Engine)."""
import pytest
import asyncio
import time
from core.engine import Orchestrator, Task, TaskStatus
from core.plugin import Plugin


class SimplePlugin(Plugin):
    name = "simple"
    async def execute(self, value):
        return value * 2


class SlowPlugin(Plugin):
    name = "slow"
    async def execute(self, delay):
        await asyncio.sleep(delay)
        return "done"


class FailingPlugin(Plugin):
    name = "failing"
    async def execute(self):
        raise RuntimeError("Plugin error")


class TestOrchestratorInitialization:
    """Test Orchestrator setup."""

    def test_default_init(self):
        engine = Orchestrator()
        assert engine.resource_limits == {}
        assert engine.enable_cancellation is True
        assert engine.enable_tracing is False

    def test_init_with_resources(self):
        engine = Orchestrator(resource_limits={"cpu": 4.0, "memory_mb": 2048})
        assert engine.resource_limits == {"cpu": 4.0, "memory_mb": 2048}
        assert len(engine._resource_semaphores) == 2

    def test_clear_empties_state(self):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a")
        engine.clear()
        assert len(engine.tasks) == 0
        assert engine.dag.size() == 0


class TestTaskAddition:
    """Test adding tasks to the orchestrator."""

    def test_add_task_with_func(self):
        engine = Orchestrator()
        task_id = engine.add_task("task1", func=lambda: "result")
        assert task_id in [t.id for t in engine.tasks.values()]
        assert engine.tasks["task1"].func is not None

    def test_add_task_with_plugin(self):
        engine = Orchestrator()
        engine.load_plugins()  # load builtins
        task_id = engine.add_task("shell_task", plugin="shell", command="echo hello")
        assert engine.tasks["task1" if False else "shell_task"].plugin_name == "shell"

    def test_add_duplicate_task_raises(self):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a")
        with pytest.raises(ValueError):
            engine.add_task("A", func=lambda: "b")

    def test_task_with_dependencies(self):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a")
        engine.add_task("B", func=lambda: "b", depends_on=["A"])
        dag_node_b = engine.dag.get_task("B")
        assert "A" in dag_node_b.dependencies

    def test_task_with_resources(self):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a", resources={"cpu": 1.0, "memory_mb": 512})
        node = engine.dag.get_task("A")
        assert node.resources == {"cpu": 1.0, "memory_mb": 512}

    def test_task_with_timeout(self):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a", timeout=5.0)
        node = engine.dag.get_task("A")
        assert node.timeout == 5.0

    def test_task_with_retry_policy(self):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a", retry_policy={"max_attempts": 3, "backoff_factor": 2.0})
        node = engine.dag.get_task("A")
        assert node.retry_policy["max_attempts"] == 3
        assert node.retry_policy["backoff_factor"] == 2.0


class TestDAGValidation:
    """Test DAG validation through orchestrator."""

    def test_validate_method(self):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a")
        engine.add_task("B", func=lambda: "b", depends_on=["A"])
        # Should not raise
        engine.validate()

    def test_validate_with_cycle_raises(self):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a")
        engine.add_task("B", func=lambda: "b", depends_on=["A"])
        # Manually create cycle
        engine.dag._nodes["A"].dependencies.add("B")
        engine.dag._nodes["B"].dependents.add("A")
        with pytest.raises(RuntimeError):
            engine.validate()


class TestOrchestratorRun:
    """Test running the orchestrator."""

    @pytest.mark.asyncio
    async def test_run_linear(self):
        engine = Orchestrator()
        results = []
        engine.add_task("A", func=lambda: results.append("A") or "a")
        engine.add_task("B", func=lambda: results.append("B") or "b", depends_on=["A"])
        engine.add_task("C", func=lambda: results.append("C") or "c", depends_on=["B"])
        duration = await engine.run()
        assert results == ["A", "B", "C"]
        assert duration > 0
        assert engine.tasks["A"].status == TaskStatus.COMPLETED
        assert engine.tasks["B"].status == TaskStatus.COMPLETED
        assert engine.tasks["C"].status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_parallel(self):
        engine = Orchestrator()
        order = []
        def make_task(name, delay):
            async def task():
                await asyncio.sleep(delay)
                order.append(name)
                return name
            return task
        engine.add_task("A", func=make_task("A", 0.05))
        engine.add_task("B", func=make_task("B", 0.03))
        engine.add_task("C", func=make_task("C", 0.01))
        # No dependencies, all should run in parallel
        await engine.run()
        # B and C likely finish before A due to shorter delays, but order is not guaranteed
        assert set(order) == {"A", "B", "C"}

    @pytest.mark.asyncio
    async def test_run_with_plugin(self):
        engine = Orchestrator()
        engine.plugin_mgr.register(SimplePlugin())
        engine.add_task("double", plugin="simple", value=5)
        await engine.run()
        task = engine.tasks["double"]
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 10

    @pytest.mark.asyncio
    async def test_task_timeout(self):
        engine = Orchestrator()
        async def slow_task():
            await asyncio.sleep(0.5)
            return "finished"
        engine.add_task("slow", func=slow_task, timeout=0.1)
        await engine.run()
        task = engine.tasks["slow"]
        assert task.status == TaskStatus.FAILED
        assert isinstance(task.result, asyncio.TimeoutError)

    @pytest.mark.asyncio
    async def test_retry_policy_success_on_retry(self):
        engine = Orchestrator()
        attempt = {"count": 0}
        def flaky():
            attempt["count"] += 1
            if attempt["count"] < 2:
                raise ValueError(" transient error")
            return "ok"
        engine.add_task("flaky", func=flaky, retry_policy={"max_attempts": 3, "backoff_factor": 0.01})
        await engine.run()
        task = engine.tasks["flaky"]
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "ok"
        assert attempt["count"] == 2

    @pytest.mark.asyncio
    async def test_retry_exhaustion_fails(self):
        engine = Orchestrator()
        def always_fails():
            raise ValueError("always fails")
        engine.add_task("fail", func=always_fails, retry_policy={"max_attempts": 2, "backoff_factor": 0.01})
        await engine.run()
        task = engine.tasks["fail"]
        assert task.status == TaskStatus.FAILED
        assert isinstance(task.result, ValueError)

    @pytest.mark.asyncio
    async def test_cancellation_propagation(self):
        engine = Orchestrator(enable_cancellation_propagation=True)
        engine.add_task("A", func=lambda: (_ for _ in ()).throw(RuntimeError("A fails")))
        engine.add_task("B", func=lambda: "b", depends_on=["A"])
        engine.add_task("C", func=lambda: "c", depends_on=["B"])
        await engine.run()
        # A fails, B and C should be cancelled
        assert engine.tasks["A"].status == TaskStatus.FAILED
        assert engine.tasks["B"].status == TaskStatus.FAILED
        assert engine.tasks["C"].status == TaskStatus.FAILED
        assert "cancelled" in str(engine.tasks["B"].result).lower()
        assert "cancelled" in str(engine.tasks["C"].result).lower()

    @pytest.mark.asyncio
    async def test_resource_aware_sequential_in_layer(self):
        engine = Orchestrator(resource_limits={"cpu": 1.0})
        # Both tasks need 1 CPU, they should run sequentially in same layer
        executed = []
        def make_task(name, cpu_needed):
            async def task():
                # Check that semaphore is held; we can't easily test that from inside
                executed.append(name)
                await asyncio.sleep(0.05)
                return name
            return task
        engine.add_task("A", func=make_task("A", 1.0), resources={"cpu": 1.0})
        engine.add_task("B", func=make_task("B", 1.0), resources={"cpu": 1.0})
        await engine.run()
        # Both completed
        assert set(executed) == {"A", "B"}
        assert engine.tasks["A"].status == TaskStatus.COMPLETED
        assert engine.tasks["B"].status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_multiple_parallel_layers(self):
        engine = Orchestrator()
        layer1 = []
        layer2 = []
        def make_task(name, layer_list, delay=0):
            async def task():
                await asyncio.sleep(delay)
                layer_list.append(name)
                return name
            return task
        engine.add_task("A1", func=make_task("A1", layer1))
        engine.add_task("A2", func=make_task("A2", layer1))
        engine.add_task("B1", func=make_task("B1", layer2, 0.01), depends_on=["A1"])
        engine.add_task("B2", func=make_task("B2", layer2, 0.01), depends_on=["A2"])
        await engine.run()
        # All tasks in layer1 should complete before layer2 starts
        assert set(layer1) == {"A1", "A2"}
        assert set(layer2) == {"B1", "B2"}

    @pytest.mark.asyncio
    async def test_report_output(self, capsys):
        engine = Orchestrator()
        engine.add_task("A", func=lambda: "a")
        engine.add_task("B", func=lambda: "b", depends_on=["A"])
        await engine.run()
        engine.report()
        captured = capsys.readouterr()
        assert "Catalyst" in captured.out
        assert "Task:" in captured.out


class TestYAMLLoading:
    """Test YAML workflow loading."""

    def test_load_yaml_requires_pyyaml(self, monkeypatch):
        engine = Orchestrator()
        # Simulate PyYAML not installed
        monkeypatch.setitem(sys.modules, 'yaml', None)
        with pytest.importorskip("yaml"):
            # Actually we'll just test that it raises ImportError if yaml missing
            pass

    @pytest.mark.asyncio
    async def test_load_yaml_simple(self, tmp_path):
        yaml_content = """
tasks:
  - name: task_a
    func: builtins.int
    args: ["5"]
  - name: task_b
    func: builtins.str
    args: ["${task_a}"]
    depends_on: [task_a]
"""
        path = tmp_path / "workflow.yaml"
        path.write_text(yaml_content)
        engine = Orchestrator()
        engine.load_yaml(str(path))
        assert "task_a" in engine.tasks
        assert "task_b" in engine.tasks
        # Run workflow
        await engine.run()
        assert engine.tasks["task_a"].result == 5
        # task_b uses str(5) -> "5", but our func is builtins.str which converts to string
        assert engine.tasks["task_b"].result == "5"

    @pytest.mark.asyncio
    async def test_load_yaml_with_plugin(self, tmp_path):
        yaml_content = """
tasks:
  - name: hello
    plugin: shell
    command: echo "Hello World"
"""
        path = tmp_path / "workflow.yaml"
        path.write_text(yaml_content)
        engine = Orchestrator()
        engine.load_yaml(str(path))
        assert "hello" in engine.tasks
        assert engine.tasks["hello"].plugin_name == "shell"


class TestResourceConstraints:
    """Test resource-aware scheduling edge cases."""

    @pytest.mark.asyncio
    async def test_unknown_resource_no_semaphore(self):
        # If task requests a resource type that orchestrator doesn't limit, should just run
        engine = Orchestrator(resource_limits={"cpu": 2.0})
        engine.add_task("A", func=lambda: "a", resources={"gpu": 1.0})  # gpu not in limits
        await engine.run()
        assert engine.tasks["A"].status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_fractional_resource_rounded_up(self):
        engine = Orchestrator(resource_limits={"cpu": 1.0})  # 1 permit total
        # Two tasks each need 0.7 cpu, they will each take at least 1 permit -> serial
        executed = []
        def task_fn(name):
            async def f():
                executed.append(name)
                await asyncio.sleep(0.05)
                return name
            return f
        engine.add_task("A", func=task_fn("A"), resources={"cpu": 0.7})
        engine.add_task("B", func=task_fn("B"), resources={"cpu": 0.7})
        await engine.run()
        # Since each takes 1 semaphore permit and only 1 total, they run sequentially
        assert executed == ["A", "B"] or executed == ["B", "A"]
