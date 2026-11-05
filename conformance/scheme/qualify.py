#!/usr/bin/env python3
"""Final fragment ladder, with the sample scoreboard last; no whole suites."""
import json
from pathlib import Path
import subprocess
import sys
from runner import ROOT


def run(*args):
    subprocess.run([sys.executable, '-B', *args], cwd=ROOT, check=True,
                   stdin=subprocess.DEVNULL)


def main():
    run('conformance/scheme/audit.py', 'source')
    run('conformance/scheme/test_context.py')
    run('conformance/scheme/test_exact.py')
    for name in ['basic', 'control', 'values', 'numeric', 'quotation', 'apply']:
        run('conformance/scheme/check.py', 'example/scheme/' + name + '.scm',
            '--evidence', '../evidence/final-' + name)
    run('conformance/scheme/check.py', 'example/scheme/tail.scm', '--tail',
        '--evidence', '../evidence/final-tail')
    run('conformance/scheme/check.py', 'example/scheme/refusal.scm', '--refusal',
        '--evidence', '../evidence/final-refusal')
    run('conformance/scheme/score.py', '--suite', 'example/scheme/score-fixture.scm',
        '--evidence', '../evidence/final-score-fragment')
    small = json.loads((ROOT.parent / 'evidence/final-score-fragment/results.json').read_text())
    assert small['passed'] == small['total'] == 5
    run('conformance/scheme/score.py', '--suite', 'example/scheme/score-state.scm',
        '--evidence', '../evidence/final-score-state')
    state = json.loads((ROOT.parent / 'evidence/final-score-state/results.json').read_text())
    assert state['total'] == 7 and state['passed'] == 6
    assert state['results'] == {'0': 'FAIL', **{str(i): 'PASS' for i in range(1, 7)}}
    run('conformance/scheme/score.py', '--sample', '10')
    sample = json.loads((ROOT.parent / 'evidence/score/results.json').read_text())
    assert sample['textual_sites'] == 989 and sample['executable_tests'] == 980
    assert sample['total'] == 99 and sample['passed'] >= 30


if __name__ == '__main__':
    main()
