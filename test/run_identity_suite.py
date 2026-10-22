#!/usr/bin/env python3
"""Run a compiler suite and reject any change to its established skip list."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_receipt import require

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('suite', choices=['llvm', 'wasm'])
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
command = [f'test/run_{args.suite}_suite.sh']
with (args.output / 'suite.txt').open('w') as log:
    result = subprocess.run(command, env=dict(os.environ, JOBS='2', COMPILER='./out/lang_next'), stdout=log, stderr=subprocess.STDOUT)
text = (args.output / 'suite.txt').read_text()
print(text)
require(result.returncode == 0, 'suite failed')
key = ('llvm-macos' if platform.system() == 'Darwin' else 'llvm-linux') if args.suite == 'llvm' else 'llvm-wasm32'
expected = json.loads(Path('test/baseline_skips.json').read_text())[key]
actual = sorted(re.findall(r'^SKIP .+$', text, re.M))
require(actual == expected, f'skip list changed: {actual}')
(args.output / 'receipt.json').write_text(json.dumps(dict(command=command, exit=result.returncode, skips=actual, baseline=key), indent=2) + '\n')
print('PASS exact baseline skips')
