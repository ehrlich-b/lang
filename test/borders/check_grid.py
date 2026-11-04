#!/usr/bin/env python3
"""Check the coverage and evidence contracts of the borders grid."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
cells = json.loads((root / 'borders.json').read_text())['cells']
mode = sys.argv[1]
if mode == 'coverage':
    readers = 'lang minipy minilisp c forth flow lox lua tiny calc'.split()
    features = ('integers floats strings functions closures structs arrays control_flow '
                'recursion effects cross_reader_call error_location').split()
    targets = ('llvm', 'llvm-wasm', 'wasm')
    actual = [(c['reader'], c['feature'], c['target']) for c in cells]
    expected = {(r, f, t) for r in readers for f in features for t in targets}
    missing = expected - set(actual)
    extra = set(actual) - expected
    if missing or extra or len(actual) != len(set(actual)):
        raise SystemExit(f'grid incomplete: {len(missing)} missing, {len(extra)} unexpected, {len(actual) - len(set(actual))} duplicates')
    for c in cells:
        if c['status'] == 'not-applicable':
            assert c.get('reason') and '\n' not in c['reason']
        else:
            assert (root / c['fixture']).is_file()
    print(f'{len(actual)} cells accounted for')
elif mode == 'evidence':
    for c in cells:
        if c['status'] == 'wrong':
            assert c['fixture'].startswith('test/borders/bugs/') and (root / c['fixture']).is_file()
        if c['status'] == 'rejected':
            assert c.get('detail', '').strip(), f'missing diagnostic: {c}'
    print('Wrong cells have fixtures and rejections have diagnostics')
else:
    raise SystemExit('usage: check_grid.py coverage|evidence')
