#!/usr/bin/env python3
"""Keep browser identity intact across the stock compiler-Wasm suite."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_receipt import digest, require, write

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
os.chdir(root)
args.output.resolve().mkdir(parents=True, exist_ok=True)
output = Path(tempfile.mkdtemp(prefix='browser-', dir=args.output.resolve()))
env = dict(os.environ, JOBS='2', TMPDIR=str(output), LANG_ROOT=str(root))


def snapshot():
    paths = subprocess.check_output(['git', 'ls-files', 'web'], text=True).splitlines()
    return {p: digest(p) for p in paths}


before = snapshot()
for label, command in [('before', ['node', 'test/browser_identity.js', str(output / 'before')]),
                       ('suite', ['test/run_compiler_wasm.sh']),
                       ('after', ['node', 'test/browser_identity.js', str(output / 'after')])]:
    with (output / (label + '.txt')).open('wb') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    print(f'{label}: exit {result.returncode}; log {output / (label + ".txt")}', flush=True)
    require(result.returncode == 0, label + ' failed')
    require(snapshot() == before, label + ' changed tracked browser artifacts')
write(output / 'preservation.json', dict(before=before, after=snapshot()))
print('PASS browser identity before/suite/after; all tracked web files unchanged')
