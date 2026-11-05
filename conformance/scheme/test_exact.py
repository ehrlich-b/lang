#!/usr/bin/env python3
"""Exercise native equality and verify the scorer rejects rounded exact values."""
import json
from pathlib import Path
import subprocess
import sys
from runner import ROOT


def main():
    folder = ROOT.parent / 'evidence/exact-regression'
    subprocess.run([sys.executable, '-B', 'conformance/scheme/check.py',
                    'example/scheme/equality.scm', '--evidence', str(folder / 'native')],
                   cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-B', 'conformance/scheme/score.py',
                    '--suite', 'example/scheme/score-exact.scm',
                    '--evidence', str(folder / 'score')], cwd=ROOT, check=True)
    result = json.loads((folder / 'score/results.json').read_text())
    expected = {str(i): 'PASS' if 6 <= i <= 14 else 'FAIL' for i in range(16)}
    assert result['results'] == expected, result
    assert result['total'] == 16 and result['passed'] == 9, result
    print('PASS exact scalar/list/vector mismatches receive no conformance credit')


if __name__ == '__main__':
    main()
