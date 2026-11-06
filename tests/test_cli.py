import json
import tempfile
from unittest.mock import patch

import pytest

from catalyst.cli import main


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("sys.argv", ["catalyst", "version"]):
        main()
    captured = capsys.readouterr()
    assert "Catalyst Engine" in captured.out


def test_cli_benchmark(capsys: pytest.CaptureFixture[str]) -> None:
    with patch(
        "sys.argv", ["catalyst", "benchmark", "--nodes", "15", "--concurrency", "5"]
    ):
        main()
    captured = capsys.readouterr()
    assert "Catalyst Engine Benchmark" in captured.out
    assert "Total Executed Tasks: 15" in captured.out
    assert "Throughput:" in captured.out


def test_cli_run_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    dag_def = {
        "name": "cli_test_dag",
        "tasks": [
            {"name": "fetch", "operation": "echo", "payload": "hello"},
            {
                "name": "reply",
                "operation": "echo",
                "payload": "world",
                "dependencies": ["fetch"],
            },
        ],
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(dag_def, f)
        temp_path = f.name

    with patch("sys.argv", ["catalyst", "run", temp_path, "--json"]):
        main()

    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert "Running workflow 'cli_test_dag'" in captured.out
    assert '"status": "success"' in captured.out


def test_cli_validate_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    valid_dag = {
        "tasks": [
            {"name": "A"},
            {"name": "B", "dependencies": ["A"]},
        ]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(valid_dag, f)
        temp_path = f.name

    with patch("sys.argv", ["catalyst", "validate", temp_path]):
        main()

    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert "valid Directed Acyclic Graph (DAG)" in captured.out


def test_cli_validate_cycle_detection(capsys: pytest.CaptureFixture[str]) -> None:
    cycle_dag = {
        "tasks": [
            {"name": "A", "dependencies": []},
            {"name": "B", "dependencies": ["A"]},
            {"name": "A", "dependencies": ["B"]},  # Cycle
        ]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(cycle_dag, f)
        temp_path = f.name

    with (
        pytest.raises(SystemExit),
        patch("sys.argv", ["catalyst", "validate", temp_path]),
    ):
        main()

    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert "Cycle Detected" in captured.err


def test_cli_serve(capsys: pytest.CaptureFixture[str]) -> None:
    with (
        patch("sys.argv", ["catalyst", "serve", "--port", "9090"]),
        patch("uvicorn.run") as mock_uvicorn,
    ):
        main()
        assert mock_uvicorn.called
    captured = capsys.readouterr()
    assert "Starting Catalyst Server" in captured.out

def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("sys.argv", ["catalyst"]):
        main()
    captured = capsys.readouterr()
    assert "usage: catalyst" in captured.out.lower()

def test_cli_run_missing_file(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("sys.argv", ["catalyst", "run", "missing_file.json"]), pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "Workflow file not found" in captured.err

def test_cli_run_invalid_json(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write("{ invalid json")
        temp_path = f.name
    with patch("sys.argv", ["catalyst", "run", temp_path]), pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert "Error reading JSON workflow" in captured.err

def test_cli_validate_missing_file(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("sys.argv", ["catalyst", "validate", "missing_file.json"]), pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "Workflow file not found" in captured.err

def test_cli_validate_invalid_json(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write("{ invalid json")
        temp_path = f.name
    with patch("sys.argv", ["catalyst", "validate", temp_path]), pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert "Invalid JSON" in captured.err

def test_cli_validate_missing_task_definition(capsys: pytest.CaptureFixture[str]) -> None:
    valid_dag = {
        "tasks": [
            {"name": "A", "dependencies": ["missing"]},
        ]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(valid_dag, f)
        temp_path = f.name

    with (
        pytest.raises(SystemExit),
        patch("sys.argv", ["catalyst", "validate", temp_path]),
    ):
        main()

    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert "depends on unregistered task" in captured.err

def test_cli_run_workflow_operations(capsys: pytest.CaptureFixture[str]) -> None:
    dag_def = {
        "name": "cli_test_dag_ops",
        "tasks": [
            {"name": "fetch", "operation": "echo", "payload": "hello"},
            {"name": "sleep_op", "operation": "sleep", "payload": 0.01},
            {"name": "compute_op", "operation": "compute", "payload": 10},
            {"name": "compute_dep", "operation": "compute", "dependencies": ["compute_op", "compute_op"]},
            {"name": "unknown_op", "operation": "unknown", "payload": "res"},
        ],
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(dag_def, f)
        temp_path = f.name

    with patch("sys.argv", ["catalyst", "run", temp_path, "--json"]):
        main()

    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert '"status": "success"' in captured.out


def test_cli_run_workflow_fail(capsys: pytest.CaptureFixture[str]) -> None:
    dag_def = {
        "name": "cli_test_dag_fail",
        "tasks": [
            {"name": "fail_op", "operation": "fail", "payload": "err"},
        ],
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(dag_def, f)
        temp_path = f.name

    with patch("sys.argv", ["catalyst", "run", temp_path, "--json"]):
        main()

    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert '"status": "failure"' in captured.out

def test_cli_run_workflow_compute_iter(capsys: pytest.CaptureFixture[str]) -> None:
    dag_def = {
        "name": "cli_test_dag_iter",
        "tasks": [
            {"name": "gen_list", "operation": "echo", "payload": [1, 2.5, "not_num", 3]},
            {"name": "compute_op", "operation": "compute", "dependencies": ["gen_list"]},
        ],
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(dag_def, f)
        temp_path = f.name

    with patch("sys.argv", ["catalyst", "run", temp_path, "--json"]):
        main()

    captured = capsys.readouterr()
    import os
    if os.path.exists(temp_path): os.remove(temp_path)
    assert '"status": "success"' in captured.out
