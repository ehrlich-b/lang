#!/usr/bin/env python3
"""Differential C11 execution: every suite input, gcc and clang at -O2.

A compiler refusal must be located and must not leave an output artifact.
A C compiler error, runtime failure, or missing oracle is a wrong answer.
Evidence and generated C can be retained with --output outside the checkout.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(args, env=None):
    try:
        p = subprocess.Popen(args, env=env, cwd=ROOT, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True)
        try:
            output, _ = p.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            output, _ = p.communicate()
            return 124, 'timeout\n' + output.decode(errors='replace')
        return p.returncode, output.decode(errors='replace')
    except OSError as exc:
        return 127, str(exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default=os.environ.get('COMPILER', 'out/lang_next'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--fixtures', type=Path, default=Path('test/suite'))
    args = parser.parse_args()
    compiler = str((ROOT / args.compiler).resolve())
    output = args.output
    temp = None
    if output is None:
        temp = tempfile.TemporaryDirectory(prefix='lang-c-suite-', dir=os.environ.get('TMPDIR'))
        output = Path(temp.name)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    fixtures = sorted((ROOT / args.fixtures).glob('*.lang'))
    if not fixtures:
        raise SystemExit('no fixtures')

    def check(fixture):
        case = output / fixture.stem
        case.mkdir(exist_ok=True)
        source = case / 'program.c'
        env = dict(os.environ, LANGBE='c', LANGOS='linux', LANG_CACHE=str(case / 'cache'))
        code, log = run([compiler, str(fixture.relative_to(ROOT)), '-o', str(source)], env)
        (case / 'emit.log').write_text(log)
        result = {'fixture': str(fixture.relative_to(ROOT)), 'compilers': {}}
        # Historical suite oracles also spell this "Expected".
        oracle = re.search(r'^//[ \t]*(?:expect|Expected):[ \t]*(-?\d+)\b', fixture.read_text(), re.M | re.I)
        expected = int(oracle.group(1)) % 256 if oracle else None
        if expected is None:
            legacy = re.search(r'^//[ \t]*(-?\d+)[ \t]*-[ \t]*expected exit code', fixture.read_text(), re.M | re.I)
            if legacy:
                expected = int(legacy.group(1)) % 256
            # This ignored legacy fixture has a self-checking main (errors 1..6)
            # but no header oracle. Exercise it too, without editing the fixture.
            elif fixture.name == '238_ast_statements.lang':
                expected = 0
        for cc in ('gcc', 'clang'):
            status = 'wrong'
            detail = ''
            if code:
                located = re.search(r'[^\n]+:\d+:\d+: (?:error:|[^\n]*error)', log)
                if code > 0 and located and not source.exists():
                    status = 'refused'
                else:
                    detail = 'unlocated refusal, crash, or stale output'
            elif expected is None:
                detail = 'missing expectation'
            else:
                binary = case / cc
                build, detail = run([cc, '-std=c11', '-pedantic-errors', '-O2', str(source), '-o', str(binary)])
                (case / f'{cc}.build.log').write_text(detail)
                if build == 0:
                    actual, detail = run([str(binary)])
                    (case / f'{cc}.run.log').write_text(detail)
                    result['compilers'][cc] = {'status': 'correct' if actual == expected else 'wrong', 'actual': actual}
                    continue
                detail = 'C11 build failed: ' + detail[-1000:]
            result['compilers'][cc] = {'status': status, 'detail': detail}
        return result

    with ThreadPoolExecutor(max_workers=int(os.environ.get('JOBS', '2'))) as pool:
        results = list(pool.map(check, fixtures))
    bugs = [r['fixture'] for r in results if (r['compilers']['gcc']['status'], r['compilers']['gcc'].get('actual')) != (r['compilers']['clang']['status'], r['compilers']['clang'].get('actual'))]
    totals = {cc: {status: sum(r['compilers'][cc]['status'] == status for r in results)
                   for status in ('correct', 'wrong', 'refused')} for cc in ('gcc', 'clang')}
    versions = {cc: run([cc, '--version'])[1].splitlines()[0] for cc in ('gcc', 'clang')}
    receipt = {'compiler_sha256': hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
               'tools': versions, 'flags': ['-std=c11', '-pedantic-errors', '-O2'],
               'files': len(fixtures), 'totals': totals, 'bugs': bugs, 'results': results}
    (output / 'results.json').write_text(json.dumps(receipt, indent=2) + '\n')
    for cc, counts in totals.items():
        print(cc + ': ' + ', '.join(f'{status}={count}' for status, count in counts.items()))
    for r in results:
        if any(v['status'] == 'wrong' for v in r['compilers'].values()):
            print('WRONG', r['fixture'], r['compilers'])
    for bug in bugs:
        print('BUG gcc/clang divergence:', bug)
    minimum = 200 if args.fixtures == Path('test/suite') else len(fixtures)
    return int(bool(bugs) or any(c['wrong'] or c['correct'] < minimum for c in totals.values()))


if __name__ == '__main__':
    raise SystemExit(main())
