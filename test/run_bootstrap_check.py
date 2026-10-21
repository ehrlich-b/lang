#!/usr/bin/env python3
"""Run the promoting bootstrap gate in an external clone of committed HEAD.

The canonical bootstrap archives and replaces tracked roots of trust. A fresh
verification clone lets that complete without mutating the candidate under test.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--evidence', required=True)
a = p.parse_args()
root = Path(__file__).resolve().parent.parent
out = Path(a.evidence).resolve()
assert root not in out.parents and root != out, 'evidence must be outside the checkout'
out.mkdir(parents=True, exist_ok=True)
checkout = Path(tempfile.mkdtemp(prefix='bootstrap-', dir=out)) / 'repo'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
subprocess.run(['git', 'clone', '--no-hardlinks', '--quiet', str(root), str(checkout)], check=True)
subprocess.run(['git', 'checkout', '--detach', head], cwd=checkout, check=True)
print(f'Bootstrap committed HEAD {head} in {checkout}', flush=True)
with (checkout.parent / 'bootstrap.txt').open('w') as log:
    result = subprocess.run(['make', 'bootstrap', 'PUBLISH_BOOTSTRAP=0', 'JOBS=2'], cwd=checkout,
                            stdout=log, stderr=subprocess.STDOUT)
print((checkout.parent / 'bootstrap.txt').read_text(), end='')
if result.returncode:
    raise SystemExit(result.returncode)
subprocess.run(['python3', 'test/run_numeric.py', 'arithmetic', '--compiler', './out/lang',
                '--evidence', str(checkout.parent / 'numeric')], cwd=checkout, check=True)
