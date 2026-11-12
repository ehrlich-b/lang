#!/usr/bin/env python3
"""Protect the integration base and the reviewed live-verifier changes."""
import subprocess

base = '42531cc'
reviewed = '658e865'
paths = ('web/verify_live.py', 'web/test_verify_live.py', 'web/build_stdlib.js')
subprocess.run(['git', 'diff', '--exit-code', base, 'HEAD', '--',
                'bootstrap', 'web', *(':(exclude)' + p for p in paths)], check=True)
for path in paths[:2]:
    actual = subprocess.check_output(['git', 'show', 'HEAD:' + path])
    expected = subprocess.check_output(['git', 'show', reviewed + ':' + path])
    if actual != expected:
        raise SystemExit(path + ': unexpected change to protected input')
path = paths[2]
actual = subprocess.check_output(['git', 'show', 'HEAD:' + path])
expected = subprocess.check_output(['git', 'show', base + ':' + path])
anchor = b"  'std/reader_diagnostics.lang',\n"
assert expected.count(anchor) == 1
expected = expected.replace(anchor, anchor + b"  'std/reader_diagnostic_width.lang',\n")
if actual != expected:
    raise SystemExit(path + ': unexpected change to protected input')
print('Protected inputs match the integration base and reviewed verifier.')
