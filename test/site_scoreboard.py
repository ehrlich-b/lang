#!/usr/bin/env python3
"""Check the published bytes, input sensitivity, and compact-row boundaries."""
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('scoreboard', ROOT / 'web/generate_scoreboard.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
generator.update(check=True)
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    for name in ('HILLCLIMB.jsonl', 'SHOWCASE.json', 'borders.json'):
        (root / name).write_bytes((ROOT / name).read_bytes())
    original = generator.rows(root)
    metrics = json.loads((root / 'SHOWCASE.json').read_text())
    history = [json.loads(line) for line in (root / 'HILLCLIMB.jsonl').read_text().splitlines()]
    history[-1].update(passing=7, total=19)
    for metric in metrics['metrics']:
        if metric['name'].startswith('clox suite'):
            metric['value'] = 7
    (root / 'HILLCLIMB.jsonl').write_text('\n'.join(json.dumps(row) for row in history))
    (root / 'SHOWCASE.json').write_text(json.dumps(metrics))
    assert ('lox', 'Crafting Interpreters · clox', '7/19', 'LLVM') in generator.rows(root)
    assert generator.rows(root) != original
    metrics['metrics'][0].update(value=2, detail='2/17 LLVM, 2/17 direct Wasm; fixture suite')
    (root / 'SHOWCASE.json').write_text(json.dumps(metrics))
    assert ('lua', 'fixture suite', '2/17', 'direct Wasm') in generator.rows(root)
    borders = json.loads((root / 'borders.json').read_text())
    borders['cells'].append({'reader': 'a very long reader <with> punctuation', 'target': 'future-target'})
    (root / 'borders.json').write_text(json.dumps(borders))
    assert any(row[2:] == ('not measured', 'future-target') for row in generator.rows(root))
for count in (0, 1, generator.LIMIT, generator.LIMIT + 1):
    rendered = generator.render([('long reader <name>', 'external suite with a long title', 'not measured', 'llvm')]*count)
    assert rendered.count('<tr>') == count + (0 if count == 0 else 1 if count <= generator.LIMIT else 2)
    assert ('<summary>' in rendered) == (count > generator.LIMIT)
    assert '<name>' not in rendered
print('PASS scoreboard regeneration, all three input sources, escaping, and 0/1/limit/overflow rows')
