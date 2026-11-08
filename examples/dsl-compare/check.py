#!/usr/bin/env python3
"""Validate comparison contracts, recorded outcomes, and commit provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'examples/dsl-compare'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def check_report(path):
    report = json.loads(path.read_text())
    assert report['head'] == git('rev-parse', 'HEAD')
    assert report['mode'] == 'full' and report['status'] == 'PASS'
    assert set(report['arms']) == {'lang', 'yacc', 'antlr', *(('lang-sdk',) if 'sdk' in report else ())}
    if 'sdk' in report:
        assert report['sdk']['commit'] == report['head']
    assert report['large_input']['lines'] == 100000
    transcript = Path(report['command_log'])
    assert transcript.name == str(transcript), 'Transcript must be beside the report'
    rows = [json.loads(s) for s in (path.parent / transcript).read_text().splitlines()]
    for arm, row in report['arms'].items():
        assert row['sample']['status'] == 'PASS'
        assert row['binary_bytes'] > 0 and row['clean_to_binary_seconds'] > 0
        assert row['handwritten_lines'] > 0 and row['generated_frontend_lines'] > 0
        assert len(row['runtime_seconds']) == 5
        assert len(row['diagnostics']) == 5
        for diagnostic in row['diagnostics'].values():
            assert diagnostic['exit_code'] == 1 and diagnostic['stderr'] and not diagnostic['stdout']
        for version in ('comments', 'baseline_comments'):
            probes = row[version]
            assert set(probes) == {'lf', 'crlf', 'cr', 'mixed'}
            for probe in probes.values():
                assert probe['status'] == 'PASS' and probe['run']['exit_code'] == 0
                assert any(r['command'] == [probe['binary'], '0'] and r['exit_code'] == 0
                           and r['stdout_text'] == '10\n' for r in rows)
        change = row['operator_change']
        assert change['baseline']['status'] == 'PASS' and change['lines_touched'] > 0
        for probe in (change['probes']['decimal'], change['baseline_decimal']):
            assert probe['status'] == 'PASS'
            assert any(r['command'] == [probe['binary'], '0'] and r['exit_code'] == 0
                       and r['stdout_text'] == '-23\n' for r in rows)
        if arm in ('lang', 'lang-sdk'):
            expansion = row['loc_expansion']
            assert expansion['exit_code'] == 0
            # The LOC-only pass must follow the sample's native link in the transcript.
            commands = [r['command'] for r in rows]
            assert commands.index(expansion['command']) > commands.index(row['sample']['native']['command'])
        assert change['baseline_rejects_remainder']['exit_code'] == 1
        assert change['lines_touched'] == change['added'] + change['removed']
        large = row['large_compile']
        assert large['status'] == 'PASS' and large['seconds'] < 180
        assert row['large_lines_per_second'] == 100000 / large['seconds']
        assert large['peak_rss_bytes'] > 0
        assert row['large_run']['exit_code'] == 0
        assert any(r['command'] == [large['binary'], '4'] and r['exit_code'] == 0
                   and r['stdout_text'] == '100000\n' for r in rows)
        for phase in ('frontend', 'native') + (('lowering',) if arm in ('lang', 'lang-sdk') else ()):
            assert large[phase]['exit_code'] == 0 and large[phase]['peak_rss_bytes'] > 0

        print(arm, row['status'], 'scale:', row['large_compile']['status'],
              'change:', change['lines_touched'], 'lines')
    for name, expected in report['input_hashes'].items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == expected
    # The self-contained transcript retains errors and hashes even if builds are reclaimed.
    assert all('stderr_text' in r and 'artifact_sha256' in r for r in rows)
    scale = json.loads((path.parent / 'scale.json').read_text())
    assert scale['head'] == report['head'] and scale['lines'] == 100000
    assert scale['historical_seconds'] == dict(bison=0.635, antlr=10.465)
    for arm, row in report['arms'].items():
        measured = scale['arms'][arm]
        assert measured['status'] == 'PASS'
        assert measured['total_seconds'] == row['large_compile']['seconds']
        assert measured['peak_rss_bytes'] == row['large_compile']['peak_rss_bytes']
    print('Validated', len(rows), 'recorded commands and', len(report['input_hashes']), 'input hashes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=('host', 'report', 'policy'))
    parser.add_argument('--report', type=Path)
    parser.add_argument('--relocate', action='store_true', help='Validate only a relocated report and transcript')
    args = parser.parse_args()
    if args.case == 'host':
        host = platform.node()
        print('hostname:', host)
        assert host != 'forge', 'Compiler test gate requires a suitable host when hostname is exactly forge'
        print('Ordinary compiler checks allowed; no privileged device or module checks used')
    elif args.case == 'report':
        assert args.report is not None
        if args.relocate:
            with tempfile.TemporaryDirectory(prefix='retained-report-', dir=args.report.resolve().parent) as folder:
                copied = Path(folder) / args.report.name
                transcript = Path(json.loads(args.report.read_text())['command_log'])
                assert transcript.name == str(transcript)
                shutil.copy2(args.report, copied)
                shutil.copy2(args.report.parent / transcript, Path(folder) / transcript)
                shutil.copy2(args.report.parent / 'scale.json', Path(folder) / 'scale.json')
                check_report(copied)
                print('Validated relocated report and sibling transcript without build artifacts')
        else:
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
