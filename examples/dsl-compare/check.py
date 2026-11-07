#!/usr/bin/env python3
"""Validate comparison contracts, recorded outcomes, and commit provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'examples/dsl-compare'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def check_report(path):
    report = json.loads(path.read_text())
    assert report['head'] == git('rev-parse', 'HEAD')
    assert report['mode'] == 'full' and report['status'] == 'PASS'
    assert set(report['arms']) == {'lang', 'yacc', 'antlr'}
    assert report['large_input']['lines'] == 100000
    rows = [json.loads(s) for s in Path(report['command_log']).read_text().splitlines()]
    for arm, row in report['arms'].items():
        assert row['sample']['status'] == 'PASS'
        assert row['binary_bytes'] > 0 and row['clean_to_binary_seconds'] > 0
        assert row['handwritten_lines'] > 0 and row['generated_frontend_lines'] > 0
        assert len(row['runtime_seconds']) == 5
        assert len(row['diagnostics']) == 5
        for diagnostic in row['diagnostics'].values():
            assert diagnostic['exit_code'] == 1 and diagnostic['stderr'] and not diagnostic['stdout']
        change = row['operator_change']
        assert change['baseline']['status'] == 'PASS' and change['lines_touched'] > 0
        assert change['baseline_rejects_remainder']['exit_code'] == 1
        assert change['lines_touched'] == change['added'] + change['removed']
        if row['large_compile']['status'] != 'PASS':
            assert arm == 'lang' and row['status'] == 'MEASURED_LIMIT'
            assert '(code ast-nodes)' in row['large_failure']
        print(arm, row['status'], 'scale:', row['large_compile']['status'],
              'change:', change['lines_touched'], 'lines')
    for name, expected in report['input_hashes'].items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == expected
    # The self-contained transcript retains errors and hashes even if builds are reclaimed.
    assert all('stderr_text' in r and 'artifact_sha256' in r for r in rows)
    print('Validated', len(rows), 'recorded commands and', len(report['input_hashes']), 'input hashes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=('host', 'report', 'policy'))
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.case == 'host':
        host = platform.node()
        print('hostname:', host)
        assert host != 'forge', 'Compiler test gate requires a suitable host when hostname is exactly forge'
        print('Ordinary compiler checks allowed; no privileged device or module checks used')
    elif args.case == 'report':
        assert args.report is not None
        check_report(args.report)
        doc = (ROOT / 'docs/compare-yacc-antlr.md').read_text()
        for phrase in ('would not pick Lang', 'documentation', 'IDE', 'ecosystem',
                       'grammar diagnostics', 'top three', 'ast-nodes'):
            assert phrase in doc, phrase
        print('Comparison includes losses, tooling gaps, and three priorities')
    else:
        identity = 'Bryan Ehrlich <ehrlich.bryan@gmail.com>'
        rows = git('log', '--format=%an <%ae>|%cn <%ce>|%s', '71ac98b..HEAD').splitlines()
        assert rows
        for row in rows:
            author, committer, subject = row.split('|', 2)
            assert author == committer == identity, row
            assert subject.endswith('.') and '\n' not in subject
        changed = git('diff', '--name-only', '71ac98b', 'HEAD').splitlines()
        assert all(p.startswith('examples/dsl-compare/') or p == 'docs/compare-yacc-antlr.md' for p in changed)
        assert not git('status', '--porcelain')
        print('All', len(rows), 'commits authored and committed by', identity)
        print('Changes confined to comparison example and documentation; source checkout clean')
        print('Headless choices: native integer tariff policy; Python ANTLR target; same Clang flags')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
