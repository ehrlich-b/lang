#!/usr/bin/env python3
"""Render the published capability cells from borders.json."""
import argparse
import collections
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START = '  <!-- borders:start -->'
END = '  <!-- borders:end -->'

def render():
    cells = json.loads((ROOT / 'borders.json').read_text())['cells']
    counts = collections.Counter(c['status'] for c in cells)
    esc = lambda s: html.escape(str(s), quote=True)
    lines = [START, '  <section id="borders" aria-labelledby="borders-title">',
             '    <h2 id="borders-title">where the borders are</h2>',
             '    <p>' + str(len(cells)) + ' tested combinations · ' + ' · '.join(f'{count} {esc(status)}' for status, count in sorted(counts.items())) + '</p>',
             '    <div class="border-grid">']
    for cell in cells:
        lines.append('      <div class="border-cell"><b>' + esc(cell['reader']) + ' / ' + esc(cell['feature']) + '</b><span>' + esc(cell['target']) + ' · ' + esc(cell['status']) + '</span></div>')
    lines += ['    </div>', '  </section>', END]
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'web/index.html'
    text = path.read_text()
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    updated = before + render() + after
    if args.check:
        if text != updated:
            raise SystemExit('borders section is stale; run python3 web/generate_borders.py')
    else:
        path.write_text(updated)

if __name__ == '__main__':
    main()
