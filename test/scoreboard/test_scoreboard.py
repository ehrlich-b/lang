#!/usr/bin/env python3
"""Small regression checks for scoreboard aggregation and publication."""
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('scoreboard', root / 'scripts/scoreboard.py')
scoreboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scoreboard)
assert scoreboard.counts('case 1/2\nTOTAL 17/30\n') == (17, 30)
assert scoreboard.counts('Passed: 220 / 250\n') == (220, 250)
assert scoreboard.counts('232/300 passed\n') == (232, 300)
assert scoreboard.counts('no aggregate') is None
cells = [{'status': status} for status, n in [('supported', 14), ('rejected', 12), ('wrong', 4), ('crash', 1)] for _ in range(n)]
assert scoreboard.border_counts(cells) == {'passed': 14, 'total': 31, 'supported': 14, 'rejected': 12, 'wrong': 4, 'crash': 1}
with tempfile.TemporaryDirectory() as directory:
    scoreboard.ROOT = Path(directory)
    (scoreboard.ROOT / 'SHOWCASE.json').write_text(json.dumps({'metrics': [
        {'name': 'clox suite tests passing, of 246', 'value': None},
        {'name': 'Lua tests passing', 'value': 0}]}))
    (scoreboard.ROOT / 'HILLCLIMB.jsonl').write_text('{"revision":"old","passing":3}\n')
    results = {'lox': {'passed': 42, 'total': 246, 'status': 'completed'},
               'lua': {'targets': {'llvm': {'passed': 3, 'total': 33}, 'wasm': {'passed': 2, 'total': 33}}},
               'borders': {'wrong': 4}}
    scoreboard.refresh(results)
    scoreboard.refresh(results)
    metrics = json.loads((scoreboard.ROOT / 'SHOWCASE.json').read_text())['metrics']
    rows = [json.loads(line) for line in (scoreboard.ROOT / 'HILLCLIMB.jsonl').read_text().splitlines()]
    assert metrics[0]['value'] == 42 and metrics[1]['value'] == 2
    assert len(rows) == 2 and rows[-1]['passing'] == 42 and rows[-1]['borders_wrong'] == 4
# A reference total followed by a failed product compilation must never publish.
with tempfile.TemporaryDirectory() as directory:
    scoreboard.ROOT = Path(directory)
    scoreboard.EVIDENCE = scoreboard.ROOT / 'evidence'
    (scoreboard.ROOT / 'SHOWCASE.json').write_text(json.dumps({'metrics': [
        {'name': 'clox suite tests passing, of 246', 'value': 58}]}))
    (scoreboard.ROOT / 'HILLCLIMB.jsonl').write_text('')
    def run(command, **kwargs):
        if command == ['make', 'lox-score']:
            return scoreboard.subprocess.CompletedProcess(command, 1, 'TOTAL 246/246\ncompile failed\n')
        return scoreboard.subprocess.CompletedProcess(command, 0, '')
    with patch.object(scoreboard.subprocess, 'run', side_effect=run), \
         patch.object(scoreboard.subprocess, 'check_output', return_value='abc\n'):
        try:
            scoreboard.main()
        except SystemExit as exc:
            assert exc.code == 1
        else:
            raise AssertionError('failed Lox run must fail the scoreboard')
    result = json.loads((scoreboard.EVIDENCE / 'scoreboard.json').read_text())['suites']['lox']
    assert result['status'] == 'error' and result['passed'] is None and result['total'] is None
    assert json.loads((scoreboard.ROOT / 'SHOWCASE.json').read_text())['metrics'][0]['value'] == 58
    assert json.loads((scoreboard.ROOT / 'HILLCLIMB.jsonl').read_text())['passing'] is None
print('scoreboard fragments passed')
