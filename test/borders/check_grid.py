#!/usr/bin/env python3
"""Validate complete coverage and the execution provenance of every cell."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
READERS = 'lang minipy minilisp c forth flow lox lua tiny calc'.split()
FEATURES = ('integers floats strings functions closures structs arrays control_flow '
            'recursion effects cross_reader_call error_location').split()
TARGETS = ('llvm', 'llvm-wasm', 'wasm')
STATUSES = {'supported', 'rejected', 'wrong', 'crash', 'not-applicable'}


def main():
    data = json.loads((ROOT / 'borders.json').read_text())
    cells = data['cells']
    mode = sys.argv[1] if len(sys.argv) == 2 else ''
    if mode == 'coverage':
        actual = [(c['reader'], c['feature'], c['target']) for c in cells]
        expected = {(r, f, t) for r in READERS for f in FEATURES for t in TARGETS}
        missing = expected - set(actual)
        extra = set(actual) - expected
        if missing or extra or len(actual) != len(set(actual)):
            raise SystemExit(f'grid incomplete: {len(missing)} missing, {len(extra)} unexpected, {len(actual) - len(set(actual))} duplicates')
        specs = json.loads((ROOT / 'test/borders/probes.json').read_text())
        assert set(specs) == {r + '/' + f for r in READERS for f in FEATURES}
        for c in cells:
            assert c['status'] in STATUSES
            if c['status'] == 'not-applicable':
                assert c.get('reason') and '\n' not in c['reason']
            else:
                assert (ROOT / c['fixture']).is_file()
        assert data['totals'] == dict(Counter(c['status'] for c in cells))
        print(f'{len(actual)} cells accounted for')
        print('Totals: ' + ', '.join(f'{k}: {v}' for k, v in sorted(data['totals'].items())))
    elif mode == 'evidence':
        minimality = json.loads((ROOT / 'test/borders/bugs/minimality.json').read_text())
        specs = json.loads((ROOT / 'test/borders/probes.json').read_text())
        for c in cells:
            path = Path(c['fixture'])
            assert not path.is_absolute() and '..' not in path.parts
            assert c['fixture_sha256'] == hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            spec = specs[c['reader'] + '/' + c['feature']]
            assert c['case_sha256'] == hashlib.sha256((ROOT / spec['fixture']).read_bytes()).hexdigest()
            assert c['expected_exit'] == spec['expected_exit'] and c['expected_stdout'] == spec['expected_stdout']
            if c['status'] == 'not-applicable':
                assert c['reason'] == spec['reason'] and not c.get('steps')
                continue
            assert c.get('steps'), f'missing execution evidence: {c}'
            assert all(step.get('command') and isinstance(step.get('exit_code'), int) for step in c['steps'])
            assert c['steps'][0]['command'][1] == c['fixture']
            last = c['steps'][-1]
            assert last['exit_code'] == c['exit_code']
            assert c['detail'] == last['stdout'] + last['stderr']
            if c['feature'] == 'error_location':
                assert c['phase'] == 'compile' and c['diagnostic'] == spec['diagnostic']
                matches = c['exit_code'] > 0 and bool(re.search(c['diagnostic'], c['detail']))
                assert (c['status'] == 'supported') == matches
            elif c['status'] == 'supported':
                assert c['phase'] == 'run'
                assert c['exit_code'] == c['expected_exit']
                assert last['stdout'] == c['expected_stdout'] and not last['stderr']
                assert len(c['steps']) == (2 if c['target'] == 'wasm' else 3)
                assert all(s['exit_code'] == 0 for s in c['steps'][:-1])
            if c['status'] in ('wrong', 'crash'):
                assert c['fixture'].startswith('test/borders/bugs/')
                assert c['fixture'] in minimality
                assert minimality[c['fixture']]['sha256'] == c['fixture_sha256']
            if c['status'] == 'rejected':
                assert c['phase'] in ('compile', 'link') and c['exit_code'] > 0
                assert c.get('detail', '').strip(), f'missing diagnostic: {c}'
        print(f'{len(cells)} cells have source hashes and stage evidence; wrong/crash cells have reduced fixtures and rejections have diagnostics')
    else:
        raise SystemExit('usage: check_grid.py coverage|evidence')


if __name__ == '__main__':
    main()
