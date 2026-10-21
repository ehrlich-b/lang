#!/usr/bin/env python3
"""Retain regression evidence; isolate the promoting bootstrap from the checkout."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('gate', choices=['bootstrap', 'llvm', 'wasm'])
options = parser.parse_args()
base = Path(os.environ.get('WORKER_EVIDENCE', tempfile.gettempdir())).resolve()
base.mkdir(parents=True, exist_ok=True)
out = Path(tempfile.mkdtemp(prefix=options.gate + '-', dir=base))
env = dict(os.environ, JOBS='2', TMPDIR=str(out))
cwd = ROOT
if options.gate == 'bootstrap':
    # The canonical target promotes tracked bootstrap roots. Run the unchanged
    # target against a retained committed snapshot, keeping the input seed in
    # the working checkout intact. Nothing is restored or discarded afterward.
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    archive = out / 'source.tar'
    with archive.open('wb') as stream:
        subprocess.run(['git', '-C', str(ROOT), 'archive', head], stdout=stream, check=True)
    cwd = out / 'repo'
    cwd.mkdir()
    with tarfile.open(archive) as snapshot:
        snapshot.extractall(cwd, filter='data')
    command = ['make', 'bootstrap', 'PUBLISH_BOOTSTRAP=0', 'VERSION=' + head[:7]]
    expected_tokens = ['LLVM FIXED POINT VERIFIED', 'AST FIXED POINT VERIFIED', 'BOOTSTRAP COMPLETE']
    skip_profile = 'llvm-macos' if platform.system() == 'Darwin' else 'llvm-linux'
else:
    command = ['test/run_llvm_suite.sh' if options.gate == 'llvm' else 'test/run_wasm_suite.sh']
    expected_tokens = ['Passed:'] if options.gate == 'llvm' else ['wasm suite:']
    skip_profile = ('llvm-macos' if platform.system() == 'Darwin' else 'llvm-linux') if options.gate == 'llvm' else 'llvm-wasm32'
log = out / 'execution.txt'
with log.open('wb') as stream:
    result = subprocess.run(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
text = log.read_text(errors='replace')
print(text, end='')
expected = sorted(json.loads((ROOT / 'test/baseline_skips.json').read_text())[skip_profile])
actual = sorted(re.findall(r'^SKIP .+$', text, re.M))
passed = result.returncode == 0 and actual == expected and all(token in text for token in expected_tokens)
receipt = dict(command=command, cwd=str(cwd), exit=result.returncode,
               skips=actual, expected_skips=expected, passed=passed)
if options.gate == 'bootstrap':
    receipt['head'] = head
    receipt['fixed_point_hash_lines'] = re.findall(r'^([0-9a-f]{64})\s+([^\n]+)$', text, re.M)
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(f'{"PASS" if passed else "FAIL"} {options.gate}; evidence: {out}')
raise SystemExit(0 if passed else 1)
