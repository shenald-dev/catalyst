with open('tests/test_engine_callable_class.py', 'r') as f:
    engine_code = f.read()

import re

engine_code = re.sub(
    r'raise BaseException\("System exit"\)',
    r'raise BaseException("System exit")  # noqa: TRY002',
    engine_code
)
engine_code = re.sub(
    r'with pytest.raises\(BaseException\):',
    r'with pytest.raises(BaseException):  # noqa: B017',
    engine_code
)

with open('tests/test_engine_callable_class.py', 'w') as f:
    f.write(engine_code)
