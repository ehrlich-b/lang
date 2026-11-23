#!/usr/bin/env python3
"""Exercise every checked-in guest fixture with the public Lox runner."""
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, 'test/lox')
from score import crashed, located_diagnostics


SEMANTIC_ERRORS = {
    'class_self_cycle': "A class can't inherit from itself.",
    'initializer_result': "Can't return a value from an initializer.",
    'return_at_top': "Can't return from top-level code.",
    'super_without_base': "Can't use 'super' in a class with no superclass.",
    'this_outside_method': "Can't use 'this' outside of a class.",
}
accepted = rejected = 0
for path in sorted(Path('example/lox/test').glob('*.lox')):
    result = subprocess.run(['example/lox/run.sh', str(path)], capture_output=True,
                            text=True, timeout=30)
    details = (str(path), result.returncode, result.stdout, result.stderr)
    assert not crashed(result), details
    output = path.with_suffix('.out')
    error = path.with_suffix('.err')
    if output.is_file():
        assert result.returncode == 0 and not result.stderr, details
        assert result.stdout == output.read_text(), details
        accepted += 1
        continue
    diagnostics = located_diagnostics(path, result.stderr)
    assert diagnostics and not result.stdout, details
    rejected += 1
    if error.is_file():
        lines = error.read_text().splitlines()
        assert result.returncode == 70 and len(diagnostics) == 1, details
        assert diagnostics[0].message == lines[0], details
        if len(lines) > 1:
            assert diagnostics[0].line == int(re.fullmatch(r'\[line (\d+)\] in script', lines[1])[1]), details
    else:
        assert result.returncode == 65, details
        if path.stem in SEMANTIC_ERRORS:
            assert diagnostics[0].message.endswith(SEMANTIC_ERRORS[path.stem]), details
assert accepted >= 1 and rejected >= 5
print(f'PASS Lox fixtures ({accepted} accepted, {rejected} rejected, 0 crashes)')
