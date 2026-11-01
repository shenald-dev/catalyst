import argparse
import asyncio
import io
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation):
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation):
        pass
from collections.abc import Callable
from typing import Any

from catalyst import RetryPolicy, TaskError, WorkflowEngine


def create_sample_dag(node_count: int = 100) -> WorkflowEngine:
    """Creates a synthetic DAG with wide concurrency and chained dependencies."""
    engine = WorkflowEngine()

    async def root_task() -> str:
        return "root_data"

    engine.add_task("root", root_task)

    # Level 1: 80% of nodes depend on root
    tier_1_nodes = []
    for i in range(1, int(node_count * 0.8)):
        name = f"tier1_node_{i}"
        tier_1_nodes.append(name)

        async def worker_task(val: Any = "root_data") -> str:
            return f"processed_{val}"

        engine.add_task(name, worker_task, dependencies=["root"])

    # Level 2: Remaining nodes aggregate tier 1 nodes
    for j in range(int(node_count * 0.8), node_count):
        name = f"agg_node_{j}"
        # Depend on a subset of tier 1 nodes
        deps = tier_1_nodes[j % len(tier_1_nodes) : j % len(tier_1_nodes) + 3]

        async def agg_task(*args: Any) -> int:
            return len(args)

        engine.add_task(name, agg_task, dependencies=deps if deps else ["root"])

    return engine


def run_benchmark(args: argparse.Namespace) -> None:
    """Executes a high-load synthetic DAG benchmark and prints latency metrics."""
    node_count = args.nodes
    concurrency = args.concurrency

    print(
        f"\n⚡ Catalyst Engine Benchmark: {node_count} nodes (concurrency={concurrency or 'unbounded'})"
    )
    print("=" * 60)

    engine = create_sample_dag(node_count)
    if concurrency:
        engine.max_concurrency = concurrency

    start = time.perf_counter()
    results = asyncio.run(engine.execute())
    duration_s = time.perf_counter() - start

    failures = sum(1 for v in results.values() if isinstance(v, TaskError))
    throughput = node_count / duration_s if duration_s > 0 else float("inf")

    print(f"✅ Total Executed Tasks: {len(results)}")
    print(f"⏱️  Wall-clock Duration:  {duration_s * 1000.0:.2f} ms")
    print(f"🚀 Throughput:           {throughput:.1f} tasks/sec")
    print(f"🛡️  Failures / Errors:    {failures}")
    print("=" * 60)


def run_workflow_file(args: argparse.Namespace) -> None:
    """Loads a JSON workflow definition file, runs it, and outputs results."""
    filepath = args.file
    if not os.path.exists(filepath):
        print(f"❌ Error: Workflow file not found at {filepath!r}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ Error reading JSON workflow: {e}", file=sys.stderr)
        sys.exit(1)

    engine = WorkflowEngine(max_concurrency=data.get("max_concurrency"))
    tasks_data = data.get("tasks", [])

    for t_def in tasks_data:
        name = t_def["name"]
        deps = t_def.get("dependencies", [])
        timeout = t_def.get("timeout")
        retries = t_def.get("retries", 0)
        op = t_def.get("operation", "echo")
        payload = t_def.get("payload")

        retry_policy = RetryPolicy(max_retries=retries) if retries > 0 else None

        def make_task_fn(operation: str, p: Any) -> Callable[..., Any]:
            async def task_fn(*args: Any, **kwargs: Any) -> Any:
                if operation == "echo":
                    return p if p is not None else (args or kwargs)
                elif operation == "sleep":
                    await asyncio.sleep(float(p or 0.05))
                    return f"Slept {p}s"
                elif operation == "fail":
                    raise ValueError(p or "Forced failure")
                elif operation == "compute":
                    nums: list[float] = []
                    for item in list(args) + list(kwargs.values()):
                        if isinstance(item, (int, float)):
                            nums.append(float(item))
                        elif isinstance(item, (list, tuple, set)):
                            nums.extend(float(x) for x in item if isinstance(x, (int, float)))
                    return sum(nums) if nums else (p or 0)
                return p

            return task_fn

        engine.add_task(
            name=name,
            func=make_task_fn(op, payload),
            dependencies=deps,
            timeout=timeout,
            retry_policy=retry_policy,
        )

    print(f"🚀 Running workflow '{data.get('name', 'custom_dag')}' ({len(tasks_data)} tasks)...")
    results = asyncio.run(engine.execute())

    if args.json:
        print(json.dumps(results.to_dict(), indent=2))
    else:
        print(f"Status: {results.status.upper()} in {results.total_duration_ms:.2f}ms")
        for node, res in results.items():
            if isinstance(res, TaskError):
                print(f"  ❌ {node}: FAILED ({res.exception})")
            else:
                print(f"  ✅ {node}: {res}")


def validate_workflow_file(args: argparse.Namespace) -> None:
    """Validates workflow syntax and checks for DAG cycles without executing."""
    filepath = args.file
    if not os.path.exists(filepath):
        print(f"❌ Error: Workflow file not found at {filepath!r}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    engine = WorkflowEngine()
    tasks_data = data.get("tasks", [])

    for t_def in tasks_data:
        try:
            engine.add_task(
                name=t_def["name"],
                func=lambda: None,
                dependencies=t_def.get("dependencies", []),
            )
        except ValueError as ve:
            print(f"❌ Validation Error: {ve}", file=sys.stderr)
            sys.exit(1)

    try:
        # Check for cycles
        import graphlib
        ts = graphlib.TopologicalSorter(engine._predecessors)
        order = list(ts.static_order())
        print(f"✅ Workflow is a valid Directed Acyclic Graph (DAG) with {len(order)} tasks.")
        print(f"   Topological Order: {' -> '.join(order)}")
    except graphlib.CycleError as ce:
        print(f"❌ Cycle Detected in Workflow: {ce}", file=sys.stderr)
        sys.exit(1)


def serve_dashboard(args: argparse.Namespace) -> None:
    """Boots the FastAPI server hosting API endpoints and the real-time visual dashboard."""
    import uvicorn
    print(f"✨ Starting Catalyst Server on {args.host}:{args.port}")
    print(f"👉 Visual Dashboard: http://{args.host}:{args.port}/dashboard")
    print(f"👉 OpenAPI Docs:     http://{args.host}:{args.port}/docs")
    uvicorn.run(
        "catalyst.presentation.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def print_version(_args: argparse.Namespace) -> None:
    """Prints the Catalyst Engine version."""
    from importlib.metadata import PackageNotFoundError, version
    try:
        ver = version("catalyst")
    except PackageNotFoundError:
        ver = "1.0.0-dev"
    print(f"Catalyst Engine v{ver} (Python {sys.version.split()[0]})")


def main() -> None:
    """Entry point for the Catalyst CLI."""
    parser = argparse.ArgumentParser(
        prog="catalyst",
        description="Catalyst Engine: High-performance parallel DAG workflow platform.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run synthetic DAG execution benchmark")
    bench_parser.add_argument("--nodes", type=int, default=100, help="Number of nodes (default: 100)")
    bench_parser.add_argument("--concurrency", type=int, default=None, help="Max concurrency limit")
    bench_parser.set_defaults(func=run_benchmark)

    # run
    run_parser = subparsers.add_parser("run", help="Execute a JSON workflow definition")
    run_parser.add_argument("file", help="Path to workflow JSON file")
    run_parser.add_argument("--json", action="store_true", help="Output full JSON telemetry")
    run_parser.set_defaults(func=run_workflow_file)

    # validate
    val_parser = subparsers.add_parser("validate", help="Validate a workflow DAG for cycles")
    val_parser.add_argument("file", help="Path to workflow JSON file")
    val_parser.set_defaults(func=validate_workflow_file)

    # serve
    serve_parser = subparsers.add_parser("serve", help="Launch the API & real-time dashboard")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8080, help="Bind port (default: 8080)")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    serve_parser.set_defaults(func=serve_dashboard)

    # version
    ver_parser = subparsers.add_parser("version", help="Print version information")
    ver_parser.set_defaults(func=print_version)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
