with open('tests/test_resolve_call_args.py', 'r') as f:
    resolve_code = f.read()
import re
resolve_code = re.sub(r'def test_resolve_call_args_no_sig\(\) -> None:\n    call_args, call_kwargs = _resolve_call_args\(123, \["A"\], \{"A": 1\}\)', 'def test_resolve_call_args_no_sig() -> None:\n    call_args, call_kwargs = _resolve_call_args(123, ["A"], {"A": 1})  # type: ignore', resolve_code)
resolve_code = re.sub(r'dict', 'dict[str, int]', resolve_code)
with open('tests/test_resolve_call_args.py', 'w') as f:
    f.write(resolve_code)

with open('tests/test_fastapi_coverage.py', 'r') as f:
    coverage_code = f.read()
coverage_code = re.sub(r'def test_global_stream_cancel\(\):', 'def test_global_stream_cancel() -> None:', coverage_code)
with open('tests/test_fastapi_coverage.py', 'w') as f:
    f.write(coverage_code)
