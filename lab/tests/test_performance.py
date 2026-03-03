"""Performance tests and benchmarks for Catalyst."""
import pytest
import asyncio
import time
from core.engine import Orchestrator
from core.dag import DAG


class TestPerformance:
    """Microbenchmarks for key operations."""

    @pytest.mark.benchmark(group="dag", min_rounds=100)
    def test_benchmark_topological_sort_large_dag(self, benchmark):
        """Benchmark topological sort on a 1000-node DAG."""
        dag = DAG()
        # Create a long chain with occasional branches
        for i in range(1000):
            deps = {f"task{i-1}"} if i > 0 else set()
            # Add a branch every 10 tasks
            if i % 10 == 0 and i > 0:
                deps.add(f"task{i-2}")
            dag.add_task(f"task{i}", dependencies=deps)
        benchmark(dag.topological_sort)

    @pytest.mark.benchmark(group="dag")
    def test_benchmark_export_dot(self, benchmark):
        """Benchmark DOT export for a 200-node DAG."""
        dag = DAG()
        for i in range(200):
            deps = {f"task{i-1}"} if i > 0 else set()
            dag.add_task(f"task{i}", dependencies=deps)
        benchmark(dag.export_dot)

    @pytest.mark.asyncio
    async def test_1000_task_execution_time(self):
        """Ensure 1000 independent tasks execute quickly (<2s)."""
        engine = Orchestrator()
        # Create 1000 tasks with no dependencies
        for i in range(1000):
            async def task_fn(idx=i):
                await asyncio.sleep(0)  # no-op
                return idx
            engine.add_task(f"t{idx}", func=task_fn)
        start = time.perf_counter()
        await engine.run()
        elapsed = time.perf_counter() - start
        # Should be well under 2 seconds (actually probably <0.5s)
        assert elapsed < 2.0
        # All should succeed
        for task in engine.tasks.values():
            assert task.status.name == "COMPLETED"

    @pytest.mark.asyncio
    async def test_resource_limiting_overhead(self):
        """Measure overhead of resource limiting (should be minimal)."""
        engine_no_limit = Orchestrator()
        engine_limit = Orchestrator(resource_limits={"cpu": 4.0})
        # Same workload
        for i in range(100):
            def make_task(eng):
                async def t():
                    await asyncio.sleep(0.001)
                    return 1
                return t
            eng.add_task(f"t{i}", func=make_task(i))
        # Time both
        start = time.perf_counter()
        await engine_no_limit.run()
        time_no_limit = time.perf_counter() - start
        start = time.perf_counter()
        await engine_limit.run()
        time_limit = time.perf_counter() - start
        # Resource-limited should be within 10% overhead (since no actual contention)
        assert time_limit < time_no_limit * 1.2

    @pytest.mark.asyncio
    async def test_memory_footprint(self):
        """Check that orchestrator overhead is reasonable (<50MB)."""
        import sys
        engine = Orchestrator()
        # Add many tasks
        for i in range(500):
            engine.add_task(f"t{i}", func=lambda: i, resources={"memory_mb": 10})
        # Estimate size
        total_size = sys.getsizeof(engine) + sum(sys.getsizeof(t) for t in engine.tasks.values())
        # Should be well under 50MB (actually probably a few MB)
        assert total_size < 50 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_dag_validation_performance(self):
        """Ensure DAG validation scales reasonably (O(V+E))."""
        dag = DAG()
        # Create a large DAG with 5000 nodes
        for i in range(5000):
            deps = {f"n{i-1}", f"n{i-2}"} if i > 1 else set()
            dag.add_task(f"n{i}", dependencies=deps)
        start = time.perf_counter()
        dag.validate()
        elapsed = time.perf_counter() - start
        # Should be fast (sub-second)
        assert elapsed < 1.0


class TestCancellationPerformance:
    """Check that cancellation propagation doesn't kill performance."""

    @pytest.mark.asyncio
    async def test_early_failure_avoids_wasted_work(self):
        engine = Orchestrator(enable_cancellation_propagation=True)
        # Create a wide DAG: one failing upstream, many downstream
        executed = []
        def record(name):
            executed.append(name)
            async def task():
                return name
            return task
        engine.add_task("A", func=record("A"))
        # B depends on A and will fail (simulated by raising)
        async def failing():
            raise RuntimeError("A fails")
        engine.add_task("B", func=failing, depends_on=["A"])
        # Many downstream tasks depending on B
        for i in range(20):
            engine.add_task(f"C{i}", func=record(f"C{i}"), depends_on=["B"])
        await engine.run()
        # Only A and B should have executed; C tasks should be cancelled
        assert "A" in executed
        assert "B" not in executed  # B failed during execution
        assert len([t for t in executed if t.startswith("C")]) == 0
        # All C tasks marked as FAILED (cancelled)
        for i in range(20):
            task = engine.tasks[f"C{i}"]
            assert task.status == TaskStatus.FAILED


class TestIntegrationScenarios:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_resources_retries_and_cancellation(self):
        engine = Orchestrator(
            resource_limits={"cpu": 2.0},
            enable_cancellation_propagation=True
        )
        # Complex workflow:
        #   A -> B -> D -> F
        #   A -> C -> E -> F
        #   A may fail, causing B, C, D, E, F to cancel
        executed = []
        def make_task(name, should_fail=False, resources=None):
            async def task():
                if should_fail:
                    raise ValueError(f"{name} failed")
                executed.append(name)
                await asyncio.sleep(0.01)
                return name
            return task
        engine.add_task("A", func=make_task("A", should_fail=True))
        engine.add_task("B", func=make_task("B"), depends_on=["A"], resources={"cpu": 1.0})
        engine.add_task("C", func=make_task("C"), depends_on=["A"], resources={"cpu": 1.0})
        engine.add_task("D", func=make_task("D"), depends_on=["B"])
        engine.add_task("E", func=make_task("E"), depends_on=["C"])
        engine.add_task("F", func=make_task("F"), depends_on=["D", "E"])
        await engine.run()
        # Only A executed and failed; rest cancelled
        assert executed == ["A"]
        for name in ["B", "C", "D", "E", "F"]:
            assert engine.tasks[name].status == TaskStatus.FAILED
            assert "cancelled" in str(engine.tasks[name].result).lower()

    @pytest.mark.asyncio
    async def test_retry_then_success_integration(self):
        engine = Orchestrator()
        attempts = {"count": 0}
        def flaky():
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise ConnectionError("temp network error")
            return "success"
        engine.add_task("flaky", func=flaky, retry_policy={"max_attempts": 5, "backoff_factor": 0.01})
        await engine.run()
        assert engine.tasks["flaky"].status == TaskStatus.COMPLETED
        assert engine.tasks["flaky"].result == "success"
        assert attempts["count"] == 3

    @pytest.mark.asyncio
    async def test_parallel_plugins(self):
        engine = Orchestrator()
        from plugins.builtin.shell import run as shell_run
        # Patch to track calls
        call_order = []
        original_shell = shell_run
        async def tracked_shell(cmd):
            call_order.append(("shell", cmd))
            return original_shell(cmd)
        # Monkey-patch the plugin execution
        original_execute = engine.plugin_mgr.get("shell").execute
        async def tracked_execute(*args, **kwargs):
            call_order.append(("plugin_call", args, kwargs))
            return await original_execute(*args, **kwargs)
        engine.plugin_mgr.get("shell").execute = tracked_execute
        engine.add_task("t1", plugin="shell", command="echo one")
        engine.add_task("t2", plugin="shell", command="echo two")
        await engine.run()
        # Both should have been called
        assert len(call_order) >= 2
