#!/usr/bin/env python3
"""Publish outside-suite snapshots separately from the capability probes."""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = '  <!-- scoreboard:start -->'
END = '  <!-- scoreboard:end -->'
LIMIT = 8


def rows(root=ROOT):
    history = [json.loads(line) for line in (root / 'HILLCLIMB.jsonl').read_text().splitlines() if line.strip()]
    metrics = json.loads((root / 'SHOWCASE.json').read_text())['metrics']
    cells = json.loads((root / 'borders.json').read_text())['cells']
    targets = {}
    for cell in cells:
        targets.setdefault(cell['reader'], set()).add(cell['target'])
    result = []
    for reader in sorted(targets):
        if reader == 'lox' and history:
            score = history[-1]
            metric = next(m for m in metrics if m['name'].startswith('clox suite'))
            if metric['value'] != score['passing']:
                raise ValueError('SHOWCASE and HILLCLIMB disagree about the latest clox score')
            result.append((reader, 'Crafting Interpreters · clox', f"{score['passing']}/{score['total']}", 'LLVM'))
        elif reader == 'lua':
            metric = next(m for m in metrics if m['name'] == 'Lua tests passing')
            scores = re.findall(r'(\d+)/(\d+) (LLVM|direct Wasm)', metric['detail'])
            if not scores:
                raise ValueError('Lua metric has no per-target suite scores')
            suite = metric['detail'].split(';', 1)[1].strip()
            for passing, total, target in scores:
                if int(passing) != metric['value']:
                    raise ValueError('Lua detail and value disagree')
                result.append((reader, suite, f'{passing}/{total}', target))
        else:
            result.append((reader, '—', 'not measured', ', '.join(sorted(targets[reader]))))
    return result


def render(data):
    esc = lambda text: html.escape(str(text), quote=True)
    out = [START, '  <section id="scoreboard" aria-labelledby="scoreboard-title">',
           '    <h2 id="scoreboard-title">how much of the outside world?</h2>',
           '    <p>Outside-suite snapshots. A border probe is not a conformance score.</p>']
    if not data:
        out.append('    <p>No suites measured.</p>')
    for index, row in enumerate(data):
        if index == 0 or index == LIMIT:
            if index == LIMIT:
                out += ['    </tbody></table></div>', f'    <details><summary>+{len(data) - LIMIT} more</summary>']
            out += ['    <div class="score-scroll"><table class="scores">',
                    '      <thead><tr><th>Language</th><th>Outside suite</th><th>Score</th><th>Target</th></tr></thead><tbody>']
        out.append('      <tr>' + ''.join('<td>' + esc(value) + '</td>' for value in row) + '</tr>')
    if data:
        out.append('    </tbody></table></div>')
    if len(data) > LIMIT:
        out.append('    </details>')
    out += ['    <p class="meta">Snapshots: HILLCLIMB · SHOWCASE. Targets: borders.</p>', '  </section>', END]
    return '\n'.join(out)


def update(check=False):
    path = ROOT / 'web/index.html'
    text = path.read_text()
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    updated = before + render(rows()) + after
    if check:
        if text != updated:
            raise SystemExit('scoreboard is stale; run python3 web/generate_scoreboard.py')
    else:
        path.write_text(updated)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    update(parser.parse_args().check)
