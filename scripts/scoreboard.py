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


def counts(output):
    """Read the final aggregate, never an individual test's fraction."""
    patterns = [r'(?im)^\s*(?:total|passed|pass(?:ed)?\s+tests|score)\s*[:=]?\s*(\d+)\s*/\s*(\d+)\s*$',
                r'(?im)^\s*(\d+)\s*/\s*(\d+)\s*(?:passed|tests passed)\s*$',
                r'(?im)^\s*(\d+)\s+passed\s*(?:,|of|/)\s*(\d+)(?:\s+total)?\s*$']
    matches = [m for pattern in patterns for m in re.finditer(pattern, output)]
    if not matches:
        return None
    m = max(matches, key=lambda match: match.start())
    return int(m[1]), int(m[2])


def border_counts(cells):
    statuses = {s: sum(c['status'] == s for c in cells) for s in ('supported', 'rejected', 'wrong', 'crash')}
    return dict(passed=statuses['supported'], total=len(cells), **statuses)


def refresh(results):
    showcase = ROOT / 'SHOWCASE.json'
    data = json.loads(showcase.read_text())
    lox = results['lox']
    lua = results['lua']
    for metric in data['metrics']:
        if metric['name'].startswith('clox suite') and lox['passed'] is not None:
            metric.update(value=lox['passed'], detail=f"Whole-corpus score: {lox['passed']}/{lox['total']}")
        if metric['name'] == 'Lua tests passing' and 'targets' in lua:
            targets = lua['targets']
            metric.update(value=min(v['passed'] for v in targets.values()), detail=', '.join(f"{v['passed']}/{v['total']} {k}" for k, v in targets.items()) + '; Lua 5.4.8 official files')
    showcase.write_text(json.dumps(data, indent=2) + '\n')
    hill = ROOT / 'HILLCLIMB.jsonl'
    lines = hill.read_text().splitlines()
    revision = 'full-scoreboard-base-1d9f702'
    lines = [line for line in lines if json.loads(line).get('revision') != revision]
    row = {'revision': revision, 'passing': lox['passed'], 'total': lox['total'], 'status': lox['status']}
    for target, value in lua.get('targets', {}).items():
        row['lua_' + target] = f"{value['passed']}/{value['total']}"
    if 'wrong' in results['borders']:
        row['borders_wrong'] = results['borders']['wrong']
    lines.append(json.dumps(row, separators=(',', ':')))
    hill.write_text('\n'.join(lines) + '\n')


def main():
    EVIDENCE.mkdir(exist_ok=True)
    env = dict(os.environ, JOBS='2')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    results = {}
    started = time.monotonic()

    def run(name, command, present=True, parse=True):
        if not present:
            print(f'{name}: scorer not on this head', flush=True)
            results[name] = {'status': 'unavailable', 'passed': None, 'total': None, 'elapsed_seconds': 0}
            return
        print(f'{name}: running', flush=True)
        start = time.monotonic()
        try:
            p = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except OSError as exc:
            p = subprocess.CompletedProcess(command, 1, str(exc) + '\n')
        elapsed = round(time.monotonic() - start, 3)
        (EVIDENCE / f'{name}.log').write_text(p.stdout)
        print(p.stdout, end='', flush=True)
        result = {'status': 'completed' if p.returncode == 0 else 'error', 'exit_code': p.returncode,
                  'passed': None, 'total': None, 'elapsed_seconds': elapsed}
        if parse:
            parsed = counts(p.stdout)
            if parsed:
                result['passed'], result['total'] = parsed
            elif p.returncode == 0:
                result['status'] = 'error'
                print(f'{name}: no aggregate count found', flush=True)
        results[name] = result

    run('build', ['make', 'build'], parse=False)
    run('lox', ['make', 'lox-score'])
    path = 'conformance/c/score.py'
    run('c', ['python3', path], (ROOT / path).exists())
    path = 'conformance/lua/score.py'
    run('lua', ['python3', path, '--compiler', 'out/lang_next', '--report', str(EVIDENCE / 'lua.json')], (ROOT / path).exists(), parse=False)
    if results['lua']['status'] == 'completed':
        report = json.loads((EVIDENCE / 'lua.json').read_text())
        results['lua']['targets'] = {target: {'passed': c['passed'], 'total': c['passed'] + c['failed']} for target, c in report['totals'].items()}
        results['lua']['passed'] = sum(c['passed'] for c in results['lua']['targets'].values())
        results['lua']['total'] = sum(c['total'] for c in results['lua']['targets'].values())
    for name, path in [('scheme', 'conformance/scheme/score.py'), ('zig', 'conformance/zig/subset/run.py'), ('direct_wasm', 'test/run_direct_wasm_suite.py')]:
        run(name, ['python3', path], (ROOT / path).exists())
    path = 'test/borders/run.py'
    run('borders', ['python3', path], (ROOT / path).exists(), parse=False)
    if results['borders']['status'] == 'completed':
        cells = json.loads((ROOT / 'borders.json').read_text())['cells']
        results['borders'].update(border_counts(cells))
    refresh(results)
    (EVIDENCE / 'scoreboard.json').write_text(json.dumps({'head': head, 'jobs': 2, 'elapsed_seconds': round(time.monotonic() - started, 3), 'suites': results}, indent=2) + '\n')
    if any(r['status'] == 'error' for r in results.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
