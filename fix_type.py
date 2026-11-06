with open('tests/test_fastapi_coverage.py', 'r') as f:
    coverage_code = f.read()
import re
coverage_code = re.sub(r'def test_declarative_workflow_compute_lists\(\):', 'def test_declarative_workflow_compute_lists() -> None:', coverage_code)
coverage_code = re.sub(r'def test_declarative_workflow\(\):', 'def test_declarative_workflow() -> None:', coverage_code)
coverage_code = re.sub(r'def test_declarative_workflow_compute_fallbacks\(\):', 'def test_declarative_workflow_compute_fallbacks() -> None:', coverage_code)
coverage_code = re.sub(r'def test_declarative_workflow_fail\(\):', 'def test_declarative_workflow_fail() -> None:', coverage_code)
coverage_code = re.sub(r'def test_global_stream\(\):', 'def test_global_stream() -> None:', coverage_code)
coverage_code = re.sub(r'def test_global_stream_cancel\(\):', 'def test_global_stream_cancel() -> None:', coverage_code)
coverage_code = re.sub(r'def test_get_workflow_run_not_found\(\):', 'def test_get_workflow_run_not_found() -> None:', coverage_code)
coverage_code = re.sub(r'def test_declarative_workflow_compute_tuples\(\):', 'def test_declarative_workflow_compute_tuples() -> None:', coverage_code)
coverage_code = re.sub(r'def test_declarative_workflow_compute_sleep\(\):', 'def test_declarative_workflow_compute_sleep() -> None:', coverage_code)
coverage_code = re.sub(r'def test_health\(\):', 'def test_health() -> None:', coverage_code)
coverage_code = re.sub(r'def test_execute\(\):', 'def test_execute() -> None:', coverage_code)
coverage_code = re.sub(r'def test_dashboard\(\):', 'def test_dashboard() -> None:', coverage_code)
coverage_code = re.sub(r'def test_runs\(\):', 'def test_runs() -> None:', coverage_code)
coverage_code = re.sub(r'async def test_event_bus_full_queue\(\):', 'async def test_event_bus_full_queue() -> None:', coverage_code)

with open('tests/test_fastapi_coverage.py', 'w') as f:
    f.write(coverage_code)

with open('tests/test_fastapi_coverage_cancel.py', 'r') as f:
    cancel_code = f.read()
cancel_code = re.sub(r'async def test_sse_generator_cancel\(\):', 'async def test_sse_generator_cancel() -> None:', cancel_code)
cancel_code = re.sub(r'async def test_sse_generator_message\(\):', 'async def test_sse_generator_message() -> None:', cancel_code)
cancel_code = re.sub(r'async def run_gen\(\):', 'async def run_gen() -> None:', cancel_code)
with open('tests/test_fastapi_coverage_cancel.py', 'w') as f:
    f.write(cancel_code)

with open('tests/test_fastapi_coverage_stream.py', 'r') as f:
    stream_code = f.read()
stream_code = re.sub(r'def test_global_stream_loop\(\):', 'def test_global_stream_loop() -> None:', stream_code)
with open('tests/test_fastapi_coverage_stream.py', 'w') as f:
    f.write(stream_code)

with open('tests/test_resolve_call_args.py', 'r') as f:
    resolve_code = f.read()
resolve_code = re.sub(r'def test_resolve_call_args_no_sig\(\):', 'def test_resolve_call_args_no_sig() -> None:', resolve_code)
resolve_code = re.sub(r'def test_resolve_call_args_positional_only\(\):', 'def test_resolve_call_args_positional_only() -> None:', resolve_code)
resolve_code = re.sub(r'def test_resolve_call_args_dict_injection\(\):', 'def test_resolve_call_args_dict_injection() -> None:', resolve_code)
resolve_code = re.sub(r'def test_resolve_call_args_dict_injection_positional_only\(\):', 'def test_resolve_call_args_dict_injection_positional_only() -> None:', resolve_code)
resolve_code = re.sub(r'def test_resolve_call_args_has_var_positional_with_positional_or_keyword_and_context\(\):', 'def test_resolve_call_args_has_var_positional_with_positional_or_keyword_and_context() -> None:', resolve_code)
resolve_code = re.sub(r'def test_resolve_call_args_var_positional_with_positional_or_keyword_and_match\(\):', 'def test_resolve_call_args_var_positional_with_positional_or_keyword_and_match() -> None:', resolve_code)
resolve_code = re.sub(r'def my_func\(a, /\):', 'def my_func(a: int, /) -> None:', resolve_code)
resolve_code = re.sub(r'def my_func\(context\):', 'def my_func(context: dict) -> None:', resolve_code)
resolve_code = re.sub(r'def my_func\(inputs, /\):', 'def my_func(inputs: dict, /) -> None:', resolve_code)
resolve_code = re.sub(r'def my_func\(context, \*args\):', 'def my_func(context: dict, *args: int) -> None:', resolve_code)
resolve_code = re.sub(r'def my_func\(B, \*args\):', 'def my_func(B: int, *args: int) -> None:', resolve_code)
with open('tests/test_resolve_call_args.py', 'w') as f:
    f.write(resolve_code)

with open('tests/test_engine_callable_class.py', 'r') as f:
    engine_code = f.read()
engine_code = re.sub(r'async def test_callable_class_is_async\(\):', 'async def test_callable_class_is_async() -> None:', engine_code)
engine_code = re.sub(r'async def test_listener_coro\(\):', 'async def test_listener_coro() -> None:', engine_code)
engine_code = re.sub(r'async def test_listener_exception\(\):', 'async def test_listener_exception() -> None:', engine_code)
engine_code = re.sub(r'async def test_run_node_single_dep_cancelled\(\):', 'async def test_run_node_single_dep_cancelled() -> None:', engine_code)
engine_code = re.sub(r'async def test_run_node_single_dep_cancelled_from_source\(\):', 'async def test_run_node_single_dep_cancelled_from_source() -> None:', engine_code)
engine_code = re.sub(r'async def test_run_node_multiple_dep_exception_base_exception\(\):', 'async def test_run_node_multiple_dep_exception_base_exception() -> None:', engine_code)
engine_code = re.sub(r'async def test_run_node_multiple_dep_exception_cancelled_again\(\):', 'async def test_run_node_multiple_dep_exception_cancelled_again() -> None:', engine_code)
engine_code = re.sub(r'async def my_dep\(\):', 'async def my_dep() -> None:', engine_code)
engine_code = re.sub(r'async def my_dep1\(\):', 'async def my_dep1() -> None:', engine_code)
engine_code = re.sub(r'async def my_dep2\(\):', 'async def my_dep2() -> None:', engine_code)
engine_code = re.sub(r'async def my_listener\(event\):', 'async def my_listener(event: object) -> None:', engine_code)
engine_code = re.sub(r'def my_listener\(event\):', 'def my_listener(event: object) -> None:', engine_code)
engine_code = re.sub(r'async def __call__\(self\):', 'async def __call__(self) -> str:', engine_code)
with open('tests/test_engine_callable_class.py', 'w') as f:
    f.write(engine_code)
