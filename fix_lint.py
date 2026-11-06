with open('tests/test_cli.py', 'r') as f:
    cli_code = f.read()

import re

cli_code = re.sub(
    r'with patch\("sys.argv", \["catalyst", "run", "missing_file.json"\]\):\n        with pytest.raises\(SystemExit\):',
    r'with patch("sys.argv", ["catalyst", "run", "missing_file.json"]), pytest.raises(SystemExit):',
    cli_code
)
cli_code = re.sub(
    r'with patch\("sys.argv", \["catalyst", "run", temp_path\]\):\n        with pytest.raises\(SystemExit\):',
    r'with patch("sys.argv", ["catalyst", "run", temp_path]), pytest.raises(SystemExit):',
    cli_code
)
cli_code = re.sub(
    r'with patch\("sys.argv", \["catalyst", "validate", "missing_file.json"\]\):\n        with pytest.raises\(SystemExit\):',
    r'with patch("sys.argv", ["catalyst", "validate", "missing_file.json"]), pytest.raises(SystemExit):',
    cli_code
)
cli_code = re.sub(
    r'with patch\("sys.argv", \["catalyst", "validate", temp_path\]\):\n        with pytest.raises\(SystemExit\):',
    r'with patch("sys.argv", ["catalyst", "validate", temp_path]), pytest.raises(SystemExit):',
    cli_code
)

with open('tests/test_cli.py', 'w') as f:
    f.write(cli_code)


with open('tests/test_fastapi_coverage.py', 'r') as f:
    coverage_code = f.read()

coverage_code = re.sub(
    r'with contextlib.suppress\(BaseException\):\n        with client.stream\("GET", "/api/v1/stream"\) as response:',
    r'with contextlib.suppress(BaseException), client.stream("GET", "/api/v1/stream") as response:',
    coverage_code
)

with open('tests/test_fastapi_coverage.py', 'w') as f:
    f.write(coverage_code)
