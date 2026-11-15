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
PROPERTIES = ('file', 'line', 'column', 'expected', 'caret')


def score_diagnostic(stderr, filename, source):
    """Score visible information, not correctness, recovery, or prose quality.

    Recognize the frontends' label:line[:column]: headers. A generic label
    does not name the input file. An explicit missing token counts as expected;
    an unexpected token alone does not. A caret needs an adjacent source line.
    """
    headers = list(re.finditer(
        r'^([^:\n]+):([1-9][0-9]*):(?:([1-9][0-9]*):)?[ \t]+([^\n]*)$',
        stderr, re.MULTILINE))
    messages = '\n'.join(h[4] for h in headers)
    lines = stderr.splitlines()
    source_lines = source.split('\n')  # Keep the empty line at EOF.
    caret = any(lines[i] in source_lines and
                re.fullmatch(r'[ \t]*\^+[ \t]*', lines[i + 1]) is not None
                for i in range(1, len(lines) - 1))
    return dict(file=any(Path(h[1]).name == Path(filename).name for h in headers),
                line=bool(headers), column=any(h[3] is not None for h in headers),
                expected=bool(re.search(r'\bexpect(?:ed|ing)\s+\S|\bmissing\s+\x27[^\x27]+\x27',
                                        messages)),
                caret=caret)


def diagnostics(path):
    """Validate retained smoke/full output without requiring build artifacts."""
    report = json.loads(path.read_text())
    assert report['head'] == git('rev-parse', 'HEAD'), 'Report must measure committed HEAD'
    assert report['status'] == 'PASS' and report['mode'] in ('smoke', 'full')
    assert set(report['arms']) == {'lang', 'yacc', 'antlr'}
    transcript = Path(report['command_log'])
    assert transcript.name == str(transcript), 'Transcript must be beside report'
    calls = [json.loads(line) for line in (path.parent / transcript).read_text().splitlines()]
    fixtures = sorted((BASE / 'fixtures/invalid').glob('*.tariff'))
    assert len(fixtures) == 5
    result = dict(head=report['head'], properties=PROPERTIES, arms={})
    for arm, measured in report['arms'].items():
        assert measured['status'] == 'PASS'
        assert set(measured['diagnostics']) == {f.stem for f in fixtures}
        rows = {}
        for fixture in fixtures:
            relative = str(fixture.relative_to(BASE))
            assert report['input_hashes'][relative] == hashlib.sha256(fixture.read_bytes()).hexdigest()
            diagnostic = measured['diagnostics'][fixture.stem]
            assert diagnostic['exit_code'] == 1 and diagnostic['stderr'] and diagnostic['stdout'] == ''
            assert any(c['stderr'] == diagnostic['log'] and c['exit_code'] == 1
                       and c['stderr_text'] == diagnostic['stderr'] and c['stdout_text'] == ''
                       and c['artifact_bytes'] == 0 and not c['timeout']
                       and c['command'][-1] == str(Path(report['work']) / 'source' /
                                                  'examples/dsl-compare' / relative)
                       for c in calls), (arm, fixture.name, 'transcript mismatch')
            properties = score_diagnostic(diagnostic['stderr'], fixture.name, fixture.read_text())
            if 'properties' in diagnostic:
                assert diagnostic['properties'] == properties
            rows[fixture.name] = dict(properties=properties, score=sum(properties.values()),
                                      stderr=diagnostic['stderr'], exit_code=1, stdout='')
        result['arms'][arm] = dict(fixtures=rows, total=sum(r['score'] for r in rows.values()), maximum=25)
    if 'diagnostics_scores' in report:
        assert report['diagnostics_scores'] == {
            arm: dict(total=row['total'], maximum=row['maximum']) for arm, row in result['arms'].items()}
    return result


def diagnostics_markdown(result):
    """Stable documentation block; exact stderr is never stripped or rewritten."""
    lines = ['<!-- diagnostics:start -->\n',
             '| Fixture | Arm | File | Line | Column | Expected tokens | Source + caret | Score |\n',
             '|---|---|---:|---:|---:|---:|---:|---:|\n']
    for fixture in next(iter(result['arms'].values()))['fixtures']:
        for arm in ('lang', 'yacc', 'antlr'):
            row = result['arms'][arm]['fixtures'][fixture]
            values = ' | '.join('yes' if row['properties'][p] else 'no' for p in PROPERTIES)
            lines.append(f"| {fixture} | {arm} | {values} | {row['score']}/5 |\n")
    lines.append('\n| Arm | Total |\n|---|---:|\n')
    for arm in ('lang', 'yacc', 'antlr'):
        lines.append(f"| {arm} | {result['arms'][arm]['total']}/25 |\n")
    lines.append('\nExact stderr follows; every invocation exits **1** with empty stdout.\n')
    for fixture in next(iter(result['arms'].values()))['fixtures']:
        for arm in ('lang', 'yacc', 'antlr'):
            stderr = result['arms'][arm]['fixtures'][fixture]['stderr']
            assert stderr.endswith('\n'), 'Markdown requires a final newline; JSON retains all bytes'
            lines.append(f'\n**{fixture} — {arm}**\n\n```text\n{stderr}```\n')
    lines.append('<!-- diagnostics:end -->\n')
    return ''.join(lines)


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
    parser.add_argument('case', choices=('host', 'report', 'policy', 'diagnostics'))
    parser.add_argument('--report', type=Path)
    parser.add_argument('--relocate', action='store_true', help='Validate only a relocated report and transcript')
    parser.add_argument('--markdown', action='store_true', help='Render the diagnostics documentation block')
    parser.add_argument('--check-doc', action='store_true', help='Require the scored block to match the documentation')
    parser.add_argument('--base', default='71ac98b', help='Base commit for the policy audit')
    args = parser.parse_args()
    if args.case == 'host':
        host = platform.node()
        print('hostname:', host)
        print('Ordinary compiler checks allowed; no privileged device or module checks used')
    elif args.case == 'diagnostics':
        assert args.report is not None
        result = diagnostics(args.report)
        block = diagnostics_markdown(result)
        if args.check_doc:
            doc = (ROOT / 'docs/compare-yacc-antlr.md').read_text()
            assert doc.count('<!-- diagnostics:start -->') == 1
            assert doc.count('<!-- diagnostics:end -->') == 1
            assert block in doc, 'Regenerate the documentation from this report'
        print(block if args.markdown else json.dumps(result, indent=2))
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
        rows = git('log', '--format=%an <%ae>|%cn <%ce>|%s', args.base + '..HEAD').splitlines()
        assert rows
        for row in rows:
            author, committer, subject = row.split('|', 2)
            assert author == committer == identity, row
            assert subject.endswith('.') and '\n' not in subject
        changed = git('diff', '--name-only', args.base, 'HEAD').splitlines()
        assert all(p.startswith('examples/dsl-compare/') or p == 'docs/compare-yacc-antlr.md' for p in changed)
        assert not git('status', '--porcelain')
        print('All', len(rows), 'commits authored and committed by', identity)
        print('Changes confined to comparison example and documentation; source checkout clean')
        print('Headless choices: native integer tariff policy; Python ANTLR target; same Clang flags')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
