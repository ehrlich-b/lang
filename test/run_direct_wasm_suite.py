#!/usr/bin/env python3
"""Compile and execute every suite case with the direct Wasm backend."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
os.chdir(root)
compiler = os.environ.get('COMPILER', './out/bootstrap_verify/kernel2')
env = dict(os.environ, LANGBE='wasm', LANGOS='wasm')
counts = dict(compiled=0, correct=0, wrong=0, refused=0)
refusals = {}
with tempfile.TemporaryDirectory(prefix='lang-direct-suite-') as tmp:
    for source in sorted(Path('test/suite').glob('*.lang')):
        lines = source.read_text().splitlines()
        match = re.match(r'// (?:expect|Expected): (\d+)', lines[0])
        if not match and len(lines) > 1:
            match = re.match(r'// (\d+) - expected exit code', lines[1])
        expected = int(match.group(1)) if match else 0
        output = Path(tmp) / (source.stem + '.wasm')
        result = subprocess.run([compiler, str(source), '-o', str(output)], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode:
            reason = (result.stderr or result.stdout).strip() or f'exit {result.returncode}'
            refusals[str(source)] = reason
            counts['refused'] += 1
            print(f'REFUSED {source}: {reason}')
            continue
        counts['compiled'] += 1
        run = subprocess.run(['node', 'test/wasm_host.js', str(output)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if run.returncode == expected:
            counts['correct'] += 1
        else:
            counts['wrong'] += 1
            print(f'WRONG {source}: expected {expected}, got {run.returncode}: '
                  f'{run.stderr.decode(errors="replace").strip()}')
print(json.dumps(counts, sort_keys=True))
if os.environ.get('PARITY_JSON'):
    Path(os.environ['PARITY_JSON']).write_text(json.dumps({**counts, 'refusals': refusals}, indent=2) + '\n')
raise SystemExit(bool(counts['wrong']))
