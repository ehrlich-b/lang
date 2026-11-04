#!/usr/bin/env python3
"""Render the checked-in execution results without running the compiler."""
import collections
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def render(data):
    cells = data['cells']
    targets = list(dict.fromkeys(cell['target'] for cell in cells))
    names = {'llvm': 'LLVM x86-64', 'wasm': 'Direct Wasm', 'llvm-wasm': 'LLVM-to-Wasm'}
    lines = ['# Borders', '', 'Zig has no current reader or AIR importer.',
             'See [Zig status](../ZIG-STATUS.md) for the history.', '',
             '| Reader | Feature | ' + ' | '.join(names.get(t, t) for t in targets) + ' | macOS arm64 |',
             '| --- | --- | ' + ' | '.join('---' for _ in targets) + ' | --- |']
    groups = {}
    for cell in cells:
        key = (cell['reader'], cell['feature'])
        group = groups.setdefault(key, {})
        if cell['target'] in group:
            raise ValueError(f'duplicate cell: {key} {cell["target"]}')
        group[cell['target']] = cell
    for (reader, feature), group in groups.items():
        links = []
        for target in targets:
            cell = group.get(target)
            links.append(f'[{cell["status"]}](../{cell["fixture"]})' if cell else 'not measured')
        lines.append(f'| {reader} | {feature} | ' + ' | '.join(links) + ' | not-run-here |')
    totals = collections.Counter(cell['status'] for cell in cells)
    lines += ['', 'Totals: ' + ', '.join(f'{status}: {count}' for status, count in sorted(totals.items())) + '.', '',
              'Each measured result comes from compiling and running its fixture; a rejection is a compiler or linker error. Exit 42 is the expected result. See `borders.json` for diagnostics and exit codes.', '']
    return '\n'.join(lines)


def main():
    result = render(json.loads((ROOT / 'borders.json').read_text()))
    path = ROOT / 'docs/BORDERS.md'
    if sys.argv[1:] == ['--check']:
        if path.read_text() != result:
            raise SystemExit('docs/BORDERS.md differs from borders.json; regenerate it')
        print('Borders documentation matches borders.json')
    elif sys.argv[1:]:
        raise SystemExit('usage: render.py [--check]')
    else:
        path.write_text(result)
        print('Wrote docs/BORDERS.md')


if __name__ == '__main__':
    main()
