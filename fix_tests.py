import re

with open('tests/test_cli.py', 'r') as f:
    cli_code = f.read()

# Add os.remove to tests where NamedTemporaryFile delete=False is used
import os
for test_name in [
    'test_cli_run_workflow',
    'test_cli_validate_workflow',
    'test_cli_validate_cycle_detection',
    'test_cli_run_invalid_json',
    'test_cli_validate_invalid_json',
    'test_cli_validate_missing_task_definition',
    'test_cli_run_workflow_operations',
    'test_cli_run_workflow_fail',
    'test_cli_run_workflow_compute_iter'
]:
    cli_code = cli_code.replace(
        f'    assert',
        f'    import os\n    if os.path.exists(temp_path): os.remove(temp_path)\n    assert',
    )
with open('tests/test_cli.py', 'w') as f:
    f.write(cli_code)


with open('tests/test_resolve_call_args.py', 'r') as f:
    resolve_code = f.read()
resolve_code = resolve_code.replace(
    'call_args, call_kwargs = _resolve_call_args(my_func, ["A"], {"A": 1})',
    'call_args, call_kwargs = _resolve_call_args(my_func, ["A"], {"A": 1})\n    assert call_args == (1,)\n    assert call_kwargs == {}'
)
with open('tests/test_resolve_call_args.py', 'w') as f:
    f.write(resolve_code)

with open('tests/test_engine_callable_class.py', 'r') as f:
    engine_code = f.read()
engine_code = engine_code.replace(
    '# just getting it executed for coverage',
    'assert len(engine._listeners) == 1'
).replace(
    'await engine.execute()\n\n@pytest.mark.asyncio\nasync def test_run_node_single_dep_cancelled():',
    'res = await engine.execute()\n    assert res\n\n@pytest.mark.asyncio\nasync def test_run_node_single_dep_cancelled():'
)
with open('tests/test_engine_callable_class.py', 'w') as f:
    f.write(engine_code)

with open('tests/test_fastapi_coverage_cancel.py', 'r') as f:
    cancel_code = f.read()
cancel_code = cancel_code.replace('    import asyncio\n', '')
with open('tests/test_fastapi_coverage_cancel.py', 'w') as f:
    f.write(cancel_code)
