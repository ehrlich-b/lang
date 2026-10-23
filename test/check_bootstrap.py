#!/usr/bin/env python3
"""Run the promoting bootstrap gate in an isolated checkout of committed HEAD.

Keep every generated root and log for inspection without changing the caller's
root of trust. BOOTSTRAP_EVIDENCE_DIR chooses the parent of the retained checkout.
"""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
parent = os.environ.get('BOOTSTRAP_EVIDENCE_DIR')
if parent:
    Path(parent).mkdir(parents=True, exist_ok=True)
directory = Path(tempfile.mkdtemp(prefix='bootstrap-check-', dir=parent))
checkout = directory / 'repo'
head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
print(f'Bootstrap committed HEAD: {head}; retained checkout: {checkout}', flush=True)
subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(root), str(checkout)], check=True)
subprocess.run(['git', '-C', str(checkout), 'checkout', '--detach', head], check=True)
subprocess.run(['make', 'bootstrap', 'PUBLISH_BOOTSTRAP=0'], cwd=checkout, check=True)
