#!/usr/bin/env python3
"""Minimal async test runner for Catalyst (no pytest required)."""
import asyncio
import importlib.util
import sys
import traceback
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple
import time


@dataclass
class TestResult:
    name: str
    passed: bool
    error: str = ""
    duration: float = 0.0


class SimpleTestRunner:
    def __init__(self, tests_dir: str = "lab/tests"):
        self.tests_dir = Path(tests_dir)
        self.results: List[TestResult] = []

    def discover_tests(self) -> List[Path]:
        return list(self.tests_dir.glob("test_*.py"))

    def load_module(self, path: Path):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def is_test_function(self, name: str) -> bool:
        return name.startswith("test_") or name.startswith("benchmark_")

    async def run_async_test(self, func, *args, **kwargs):
        """Run an async test function."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync in executor to handle both
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def run_tests_in_module(self, module):
        for name in dir(module):
            if not self.is_test_function(name):
                continue
            func = getattr(module, name)
            if not callable(func):
                continue
            full_name = f"{module.__name__}.{name}"
            start = time.perf_counter()
            try:
                # Check if it's a benchmark (has benchmark attribute from pytest-benchmark)
                # In simple runner, we just run it once.
                result = await self.run_async_test(func)
                # If test has 'benchmark' attribute, skip or handle differently
                if hasattr(func, "benchmark"):
                    # This is a pytest-benchmark test; we can't run it directly
                    # Mark as skipped
                    elapsed = time.perf_counter() - start
                    self.results.append(TestResult(full_name, True, "(benchmark test - skipped)", elapsed))
                else:
                    elapsed = time.perf_counter() - start
                    self.results.append(TestResult(full_name, True, "", elapsed))
            except Exception as e:
                elapsed = time.perf_counter() - start
                error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
                self.results.append(TestResult(full_name, False, error, elapsed))

    async def run_all(self):
        test_files = self.discover_tests()
        if not test_files:
            print("No tests found!")
            return
        print(f"Found {len(test_files)} test modules")
        for path in test_files:
            try:
                module = self.load_module(path)
                await self.run_tests_in_module(module)
            except Exception as e:
                print(f"Failed to load {path}: {e}")
                self.results.append(TestResult(str(path), False, f"Load error: {e}", 0))

    def print_summary(self):
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print("\n" + "="*60)
        print(f"Test Summary: {passed}/{total} passed")
        print("="*60)
        for r in self.results:
            status = "✅ PASS" if r.passed else "❌ FAIL"
            print(f"{status} | {r.name:<60} ({r.duration:.4f}s)")
            if not r.passed:
                # Print first line of error
                lines = r.error.splitlines()
                if lines:
                    print(f"       {lines[0]}")
        print("="*60)
        return passed == total


async def main():
    runner = SimpleTestRunner()
    await runner.run_all()
    success = runner.print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
