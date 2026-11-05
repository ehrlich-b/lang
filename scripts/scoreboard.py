#!/usr/bin/env python3
"""Run the available whole-corpus scorers and retain their results."""
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT.parent / 'evidence'
EVIDENCE.mkdir(exist_ok=True)
env = dict(os.environ, JOBS='2')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
results = {}
started = time.monotonic()

def run(name, command, present=True):
    if not present:
        print(f'{name}: scorer not on this head', flush=True)
        results[name] = {'status': 'unavailable', 'passed': None, 'total': None, 'elapsed_seconds': 0}
        return ''
    print(f'{name}: running', flush=True)
    start = time.monotonic()
    p = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    elapsed = round(time.monotonic() - start, 3)
    (EVIDENCE / f'{name}.log').write_text(p.stdout)
    print(p.stdout, end='', flush=True)
    results[name] = {'status': 'completed' if p.returncode == 0 else 'error', 'exit_code': p.returncode,
                     'passed': None, 'total': None, 'elapsed_seconds': elapsed}
    return p.stdout

# Build the current compiler for the Lua and borders drivers.
run('build', ['make', 'build'])
lox = run('lox', ['make', 'lox-score'])
matches = re.findall(r'^TOTAL (\d+)/(\d+)$', lox, re.M)
if matches:
    results['lox'].update(passed=int(matches[-1][0]), total=int(matches[-1][1]))
for name, path in [('c', 'conformance/c/score.py')]:
    run(name, ['python3', path], (ROOT / path).exists())
run('lua', ['python3', 'conformance/lua/score.py', '--compiler', 'out/lang_next', '--report', str(EVIDENCE / 'lua.json')])
if results['lua']['exit_code'] == 0:
    report = json.loads((EVIDENCE / 'lua.json').read_text())
    results['lua']['targets'] = {target: {'passed': counts['passed'], 'total': counts['passed'] + counts['failed']} for target, counts in report['totals'].items()}
for name, path in [('scheme', 'conformance/scheme/score.py'), ('zig', 'conformance/zig/subset/run.py'), ('direct_wasm', 'test/run_direct_wasm_suite.py')]:
    run(name, ['python3', path], (ROOT / path).exists())
run('borders', ['python3', 'test/borders/run.py'])
if results['borders']['exit_code'] == 0:
    cells = json.loads((ROOT / 'borders.json').read_text())['cells']
    wrong = sum(c['status'] == 'wrong' for c in cells)
    results['borders'].update(passed=len(cells) - wrong, total=len(cells), wrong=wrong,
                              crashes=sum(c['status'] == 'crash' for c in cells))
(EVIDENCE / 'scoreboard.json').write_text(json.dumps({'head': head, 'jobs': 2, 'elapsed_seconds': round(time.monotonic() - started, 3), 'suites': results}, indent=2) + '\n')
if any(r['status'] == 'error' for r in results.values()):
    raise SystemExit(1)
