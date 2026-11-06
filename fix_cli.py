with open('tests/test_cli.py', 'r') as f:
    cli_code = f.read()

import re

# Remove the broken os.remove lines in tests that do not have temp_path defined
broken_tests = [
    'test_cli_version',
    'test_cli_benchmark',
    'test_cli_serve',
    'test_cli_help',
    'test_cli_run_missing_file',
    'test_cli_validate_missing_file',
]

for test_name in broken_tests:
    # We replace the specific lines inside each broken test
    # Find the function def and replace the block
    pattern = r'(def ' + test_name + r'[\s\S]*?)    import os\n    if os\.path\.exists\(temp_path\): os\.remove\(temp_path\)\n'
    cli_code = re.sub(pattern, r'\1', cli_code)

with open('tests/test_cli.py', 'w') as f:
    f.write(cli_code)
