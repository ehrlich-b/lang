#!/usr/bin/env python3
"""Runtime diagnostics must match completely, including stack frames."""
from pathlib import Path
import subprocess
import tempfile

from score import Diagnostic, located_diagnostics

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'test' / 'variable').mkdir(parents=True)
    (root / 'test' / 'variable' / 'missing.lox').write_text("missing; // expect runtime error: Undefined variable 'missing'.\n")
    interpreter = root / 'fake'
    for suffix, expected in [('', 'variable: 1/1'), ('extra failure\n', 'variable: 0/1')]:
        interpreter.write_text("#!/bin/sh\nprintf \"Undefined variable 'missing'.\\n[line 1] in script\\n%s\" >&2\nexit 70\n" % suffix.replace('\n', '\\n'))
        interpreter.chmod(0o755)
        result = subprocess.run(['python3', 'test/lox/score.py', '--suite', str(root), '--interpreter', str(interpreter)], capture_output=True, text=True)
        assert expected in result.stdout, result.stdout
print('PASS scorer runtime diagnostics')

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp, 'snippet.lox')
    path.write_text('print 1;\n\tmissing;\n')
    header = f"{path}:2:2: Undefined variable 'missing'. @10:11"
    valid = f'{header}\n\tmissing;\n\t^\n'
    assert located_diagnostics(path, valid) == [Diagnostic(2, 2, "Undefined variable 'missing'.")]
    assert not located_diagnostics(path, valid.replace('\t^', '^'))
    assert not located_diagnostics(path, valid.replace('missing;', 'changed;'))
    assert not located_diagnostics(path, valid + 'trailing error\n')
print('PASS scorer snippet validation')
