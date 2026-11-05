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
             'One small probe per feature, measured separately on each target. A pass describes that probe, not full language compatibility.',
             'LLVM x86-64 uses clang at `-O0`; LLVM-to-Wasm uses clang/wasm-ld and the shipped Node host; direct Wasm uses the same host.',
             'macOS arm64 was not executed on this host.', '',
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
            links.append(('not-applicable' if cell['status'] == 'not-applicable' else
                          f'[{cell["status"]}](../{cell["fixture"]})') if cell else 'not measured')
        lines.append(f'| {reader} | {feature} | ' + ' | '.join(links) + ' | not-run-here |')
    totals = collections.Counter(cell['status'] for cell in cells)
    if 'totals' in data and dict(totals) != data['totals']:
        raise ValueError('stored totals differ from the measured cells')
    lines += ['', 'Totals: ' + ', '.join(f'{status}: {count}' for status, count in sorted(totals.items())) + '.', '',
              'Ordinary probes compile, link, and run against explicit exit-code and stdout oracles in `test/borders/probes.json` (usually exit 42; Lox prints a value, Lua asserts). Rejected means compilation or linking failed; wrong means an oracle mismatch; crash includes target traps and timeouts.',
              'Error-location probes intentionally fail compilation: supported requires the expected guest line/column (Lox reports a line). A wrapper-file error alone is wrong. These cells do not claim successful target execution.',
              'See `borders.json` for every command, stage, exit code, source hash, stdout, stderr, and rejection diagnostic. Wrong/crash reproducers and reduction notes live in [bugs](../test/borders/bugs/README.md).', '']
    reasons = {(c['reader'], c['feature'], c['reason']) for c in cells if c['status'] == 'not-applicable'}
    for reader, feature, reason in sorted(reasons):
        lines.append(f'- {reader}/{feature}: {reason}')
    lines += ['', 'Regenerate with `COMPILER=out/lang_next python3 -B test/borders/run.py`; check this document with `python3 -B test/borders/render.py`. Filtered runs (`--reader`, `--target`, `--feature`) print fragment results without changing the published grid.', '']
    return '\n'.join(lines)


def check(path, result):
    if path.read_text() != result:
        raise ValueError('docs/BORDERS.md differs from borders.json; regenerate it')


def main():
    result = render(json.loads((ROOT / 'borders.json').read_text()))
    path = ROOT / 'docs/BORDERS.md'
    if sys.argv[1:] in ([], ['--check']):
        try:
            check(path, result)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print('Borders documentation matches borders.json')
    elif sys.argv[1:] == ['--write']:
        path.write_text(result)
        print('Wrote docs/BORDERS.md')
    else:
        raise SystemExit('usage: render.py [--check|--write]')
    data = json.loads((ROOT / 'borders.json').read_text())
    print('Totals: ' + ', '.join(f'{k}: {v}' for k, v in sorted(collections.Counter(c['status'] for c in data['cells']).items())))


if __name__ == '__main__':
    main()
