#!/usr/bin/env python3
"""Run the promoting bootstrap on an exact-HEAD disposable checkout.

Bootstrap promotes tracked roots and archives its previous root. Keeping the
full checkout and its build output preserves evidence without mutating the
candidate or needing to restore/delete generated roots after verification.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parent.parent
out = a.output.resolve()
out.mkdir(parents=True, exist_ok=True)
checkout = Path(tempfile.mkdtemp(prefix='bootstrap-', dir=out)) / 'repo'
head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=root, text=True).strip()
subprocess.run(['git','clone','--shared','--no-checkout',str(root),str(checkout)],check=True)
subprocess.run(['git','checkout','--detach',head],cwd=checkout,check=True)
env = dict(os.environ, TMPDIR=str(checkout.parent), JOBS='2', LANG_STAGE_FRESH_COMPILER='0')
with (checkout.parent/'bootstrap.log').open('wb') as log:
    result = subprocess.run(['make','bootstrap','PUBLISH_BOOTSTRAP=0'],cwd=checkout,env=env,stdout=log,stderr=subprocess.STDOUT)
print((checkout.parent/'bootstrap.log').read_text(),flush=True)
print('Bootstrap checkout and evidence: '+str(checkout.parent),flush=True)
raise SystemExit(result.returncode)
