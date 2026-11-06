#!/usr/bin/env python3
"""Protect the integration base while admitting the Wasm timing import."""
import subprocess
from pathlib import Path

paths = ('web/host.js', 'web/compiler_host.js')
subprocess.run(['git', 'diff', '--exit-code', '0149c1d', 'HEAD', '--',
                'bootstrap/current', 'web', *(':(exclude)' + p for p in paths)], check=True)
for path in paths:
    original = subprocess.check_output(['git', 'show', '0149c1d:' + path])
    expected = original.replace(b'    getpid: () => 1n,',
                                b'    clock_gettime: () => -1n,\n    realpath: () => 0,\n'
                                b'    lstat: () => -1n,\n    fcntl: () => -1n,\n'
                                b'    mkdtemp: () => 0,\n    getpid: () => 1n,')
    if expected == original or Path(path).read_bytes() != expected:
        raise SystemExit(path + ': unexpected change to protected input')
