#!/usr/bin/env python3
"""
Catalyst Performance Benchmark Suite

Run microbenchmarks for key DAG and orchestrator operations.
Helps detect performance regressions over time.

Usage:
    python benchmarks/run_benchmarks.py [--iterations N] [--output json|csv|pretty]

Requirements:
    pip install pytest-benchmark
"""

from __future__ import annotations
import argparse
import time
import statistics
from pathlib import Path
import sys

# Add catalyst to path
CATALYST_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CATALYST_ROOT))

from core.dag import DAG


def bench_topological_sort(num_nodes: int, iterations: int = 5) -> float:
    """Benchmark topological sort on a linear chain DAG."""
    times = []
    for _ in range(iterations):
        dag = DAG()
        for i in range(num_nodes):
            deps = {f"n{i-1}"} if i > 0 else set()
            dag.add_task(f"n{i}", dependencies=deps)
        start = time.perf_counter()
        dag.topological_sort()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return statistics.mean(times)


def bench_makespan_unlimited(num_nodes: int, iterations: int = 5) -> float:
    """Benchmark makespan estimation (unlimited resources) on a linear chain."""
    times = []
    for _ in range(iterations):
        dag = DAG()
        for i in range(num_nodes):
            deps = {f"n{i-1}"} if i > 0 else set()
            dag.add_task(f"n{i}", dependencies=deps, duration=1.0)
        start = time.perf_counter()
        dag.estimated_makespan()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return statistics.mean(times)


def bench_makespan_resource_constrained(num_nodes: int, iterations: int = 5) -> float:
    """Benchmark resource-aware makespan estimation on a pipeline with constraints."""
    times = []
    for _ in range(iterations):
        dag = DAG()
        # Create a pipeline: stages each need 1 CPU, but limit = 2, so 2 can run in parallel
        # For N nodes, number of layers = ceil(N/2)
        # Total duration = ceil(N/2) * 1 (if unlimited resources would be N)
        for i in range(num_nodes):
            deps = {f"n{i-1}"} if i > 0 else set()
            dag.add_task(f"n{i}", dependencies=deps, duration=1.0, resources={"cpu": 1.0})
        start = time.perf_counter()
        dag.estimated_makespan(resource_limits={"cpu": 2.0})
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return statistics.mean(times)


def bench_critical_path(num_nodes: int, iterations: int = 5) -> float:
    """Benchmark critical path calculation on a diamond-heavy DAG."""
    times = []
    for _ in range(iterations):
        dag = DAG()
        # Build a diamond pattern with varying durations
        dag.add_task("A", duration=1.0)
        for i in range(10):
            dag.add_task(f"B{i}", dependencies={"A"}, duration=0.5)
            dag.add_task(f"C{i}", dependencies={f"B{i}"}, duration=0.5)
            dag.add_task(f"D{i}", dependencies={f"C{i}"}, duration=0.5)
        # Total ~ 1 + 10*(0.5+0.5+0.5) = 1+15 = 16
        start = time.perf_counter()
        dag.critical_path()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return statistics.mean(times)


def format_result(name: str, mean: float, unit: str = "ms") -> str:
    if unit == "ms":
        val = mean * 1000
    elif unit == "us":
        val = mean * 1_000_000
    else:
        val = mean
    return f"{name:40} {val:10.4f} {unit}"


def main():
    parser = argparse.ArgumentParser(description="Run Catalyst benchmarks")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations per benchmark")
    parser.add_argument("--output", choices=["pretty", "json", "csv"], default="pretty")
    args = parser.parse_args()

    results = []

    # Define scenarios
    scenarios = [
        ("TopoSort 1000 nodes", lambda: bench_topological_sort(1000, args.iterations)),
        ("TopoSort 2000 nodes", lambda: bench_topological_sort(2000, args.iterations)),
        ("Makespan (unlimited) 1000", lambda: bench_makespan_unlimited(1000, args.iterations)),
        ("Makespan (unlimited) 2000", lambda: bench_makespan_unlimited(2000, args.iterations)),
        ("Makespan (constrained) 1000", lambda: bench_makespan_resource_constrained(1000, args.iterations)),
        ("Makespan (constrained) 2000", lambda: bench_makespan_resource_constrained(2000, args.iterations)),
        ("Critical Path (diamond)", lambda: bench_critical_path(10, args.iterations)),
    ]

    for name, func in scenarios:
        try:
            mean_sec = func()
            results.append((name, mean_sec))
        except Exception as e:
            results.append((name, f"ERROR: {e}"))

    if args.output == "pretty":
        print("\nCatalyst Benchmark Suite")
        print("=" * 70)
        print(f"{'Benchmark':40} {'Time':>12}")
        print("-" * 70)
        for name, mean_sec in results:
            if isinstance(mean_sec, float):
                # Show in ms for readability
                print(format_result(name, mean_sec, "ms"))
            else:
                print(f"{name:40} {mean_sec}")
        print("=" * 70)
    elif args.output == "json":
        import json
        payload = {name: mean_sec for name, mean_sec in results}
        print(json.dumps(payload, indent=2))
    elif args.output == "csv":
        import csv
        w = csv.writer(sys.stdout)
        w.writerow(["benchmark", "seconds"])
        for name, mean_sec in results:
            if isinstance(mean_sec, float):
                w.writerow([name, mean_sec])
            else:
                w.writerow([name, mean_sec])


if __name__ == "__main__":
    main()
