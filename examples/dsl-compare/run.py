#!/usr/bin/env python3
"""Run the three native pipelines from a fresh clone; retain commands and results."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import threading

from check import score_diagnostic

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ARMS = ('lang', 'yacc', 'antlr')
DEPENDENCIES = {
    'lang': ['Clang 23.1.5', 'Lang source and LLVM bootstrap at measured HEAD'],
    'yacc': ['Clang 23.1.5', 'flex 2.6.4', 'Bison 3.8.2', 'GNU m4 1.4.19'],
    'antlr': ['Clang 23.1.5', 'ANTLR 4.13.2 complete jar', 'Java 21.0.13+9',
              'Python 3.13', 'antlr4-python3-runtime 4.13.2'],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frontend_diff(before, after):
    names = {path.name for root in (before, after) for path in root.iterdir() if path.is_file()}
    patches, added, removed = [], 0, 0
    for name in sorted(names):
        old, new = before / name, after / name
        diff = list(difflib.unified_diff(
            old.read_text().splitlines(True) if old.is_file() else [],
            new.read_text().splitlines(True) if new.is_file() else [],
            fromfile='before/' + name, tofile='after/' + name))
        added += sum(s.startswith('+') and not s.startswith('+++') for s in diff)
        removed += sum(s.startswith('-') and not s.startswith('---') for s in diff)
        patches.extend(diff)
    return ''.join(patches), added, removed


class Experiment:
    def __init__(self, tools, report, sdk=None):
        self.tools = tools.resolve()
        self.report = report.resolve()
        if self.report.is_relative_to(REPO):
            raise ValueError('Keep reports outside the source checkout')
        self.report.parent.mkdir(parents=True, exist_ok=True)
        self.work = Path(tempfile.mkdtemp(prefix='dsl-compare-', dir=self.report.parent.parent / 'scratch'))
        self.log = self.report.parent / (self.work.name + '.commands.jsonl')
        self.env = dict(os.environ, LANGBE='llvm', LANGOS='linux',
                        PYTHONDONTWRITEBYTECODE='1',
                        BISON_PKGDATADIR=str(self.tools / 'prefix/usr/share/bison'),
                        M4=str(self.tools / 'prefix/usr/bin/m4'),
                        PYTHONPATH=str(self.tools / 'python'),
                        PATH=str(self.tools / 'llvm/bin') + os.pathsep + os.environ['PATH'])
        self.sdk = sdk.resolve() if sdk else None
        if self.sdk:
            assert (self.sdk / 'sdk.json').is_file() and (self.sdk / 'bin/lang').is_file()
        self.root = self.work / 'source'
        self.call(['git', 'clone', '--quiet', '--no-local', str(REPO), str(self.root)], cwd=self.work)
        self.base = self.root / 'examples/dsl-compare'

    def call(self, args, *, cwd=None, output=None, timeout=180, required=True, env=None):
        args = [str(a) for a in args]
        start = time.perf_counter()
        outpath = output or self.work / f'command-{len(list(self.work.glob("command-*.stdout"))):04d}.stdout'
        errpath = Path(str(outpath) + '.stderr')
        timed_out = False
        with outpath.open('wb') as out, errpath.open('wb') as err:
            try:
                process = subprocess.Popen(args, cwd=cwd or self.root, env=env or self.env,
                                           stdout=out, stderr=err, start_new_session=True)
                def expire():
                    nonlocal timed_out
                    timed_out = True
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                timer = threading.Timer(max(0.001, timeout), expire)
                timer.start()
                try:
                    _, status, usage = os.wait4(process.pid, 0)
                    process.returncode = os.waitstatus_to_exitcode(status)
                finally:
                    timer.cancel()
                    timer.join()
                code = 124 if timed_out else process.returncode
            except OSError:
                raise
        result = dict(command=args, cwd=str(cwd or self.root), exit_code=code,
                      seconds=time.perf_counter() - start, stdout=str(outpath),
                      stderr=str(errpath), timeout=timed_out,
                      peak_rss_bytes=int(usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)))
        with self.log.open('a') as log:
            log.write(json.dumps(dict(result, stderr_text=errpath.read_text(errors='replace'),
                                      stdout_text=outpath.read_text(errors='replace') if output is None else None,
                                      artifact_sha256=sha(outpath), artifact_bytes=outpath.stat().st_size)) + '\n')
        if required and code:
            raise RuntimeError(json.dumps(result) + '\n' + errpath.read_text()[-3000:])
        return result

    def build(self, arm, source, target, build_compiler=False):
        target.mkdir()
        start = time.perf_counter()
        generated = []
        if arm in ('lang', 'lang-sdk'):
            if build_compiler:
                self.call(['make', 'build'], timeout=180)
            compiler = self.sdk / 'bin/lang' if arm == 'lang-sdk' else self.root / 'out/lang_next'
            ir = target / 'reader.ll'
            self.call([compiler, source / 'tariff.lang', '-o', ir],
                      cwd=target if arm == 'lang-sdk' else None)
            self.call(['clang', '-O2', ir, '-o', target / 'frontend'])
            generated = [ir]
            frontend = [target / 'frontend']
        elif arm == 'yacc':
            self.call([self.tools / 'prefix/usr/bin/bison', '--warnings=all', '--defines=tariff.tab.h',
                       '-o', 'tariff.tab.c', source / 'tariff.y'], cwd=target)
            self.call([self.tools / 'prefix/usr/bin/flex', '-o', 'lex.yy.c', source / 'tariff.l'], cwd=target)
            generated = [target / n for n in ('tariff.tab.c', 'tariff.tab.h', 'lex.yy.c')]
            self.call(['clang', '-O2', '-I', source, '-I', target, target / 'tariff.tab.c',
                       target / 'lex.yy.c', source / 'text.c', '-o', target / 'frontend'])
            frontend = [target / 'frontend']
        else:
            # An absolute grammar path plus -Xexact-output-dir avoids nested output paths.
            self.call([self.tools / 'jre/bin/java', '-jar', self.tools / 'antlr-4.13.2-complete.jar',
                       '-Dlanguage=Python3', '-visitor', '-no-listener', '-Xexact-output-dir',
                       '-o', target, source / 'Tariff.g4'])
            generated = sorted(target.glob('*.py'))
            shutil.copy2(source / 'compile.py', target / 'compile.py')
            frontend = [sys.executable, target / 'compile.py']
        return dict(frontend=frontend, generated=generated, seconds=time.perf_counter() - start)

    def compile(self, arm, build, fixture, target):
        target.mkdir()
        start = time.perf_counter()
        emitted = target / ('program.ast' if arm in ('lang', 'lang-sdk') else 'program.c')
        front = self.call(build['frontend'] + [fixture], output=emitted, required=False)
        if front['exit_code']:
            return dict(status='TIMEOUT' if front['timeout'] else 'FAILED', frontend=front,
                        seconds=time.perf_counter() - start)
        backend = emitted
        if arm in ('lang', 'lang-sdk'):
            backend = target / 'program.ll'
            compiler = self.sdk / 'bin/lang' if arm == 'lang-sdk' else self.root / 'out/lang_next'
            lower = self.call([compiler, '--from-ast', emitted,
                               '--ast-source', fixture, '-o', backend], required=False,
                              cwd=target if arm == 'lang-sdk' else None,
                              timeout=180 - (time.perf_counter() - start))
            if lower['exit_code']:
                return dict(status='TIMEOUT' if lower['timeout'] else 'FAILED', frontend=front,
                            lowering=lower, seconds=time.perf_counter() - start)
        native = self.call(['clang', '-O2', backend, self.base / 'harness.c', '-o', target / 'program'], required=False,
                           timeout=180 - (time.perf_counter() - start))
        return dict(status='PASS' if not native['exit_code'] else 'TIMEOUT' if native['timeout'] else 'FAILED',
                    frontend=front, native=native, seconds=time.perf_counter() - start,
                    lowering=lower if arm in ('lang', 'lang-sdk') else None,
                    peak_rss_bytes=max(r['peak_rss_bytes'] for r in
                                       ([front, lower, native] if arm in ('lang', 'lang-sdk') else [front, native])),
                    binary=str(target / 'program'), binary_bytes=(target / 'program').stat().st_size
                    if not native['exit_code'] else None,
                    emitted_lines=len(emitted.read_text().splitlines()),
                    backend_lines=len(backend.read_text().splitlines()))

    def expect(self, result, n, answer):
        assert result['status'] == 'PASS', result
        run = self.call([result['binary'], str(n)])
        actual = Path(run['stdout']).read_text()
        assert actual == str(answer) + '\n', (actual, answer)
        return run

    def comments(self, arm, build, fixtures, target):
        target.mkdir()
        probes = {}
        for fixture in sorted((fixtures / 'comments').glob('*.tariff')):
            result = self.compile(arm, build, fixture, target / fixture.stem)
            result['run'] = self.expect(result, 0, 10)
            probes[fixture.stem] = result
        assert set(probes) == {'lf', 'crlf', 'cr', 'mixed'}
        return probes

    def run(self, smoke):
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.root, text=True).strip()
        report = dict(version=1, head=head, host=platform.node(), platform=platform.platform(),
                      mode='smoke' if smoke else 'full', flags=['-O2'], work=str(self.work),
                      command_log=self.log.name, arms={}, input_hashes={}, dependencies=DEPENDENCIES,
                      shared_build_dependencies=['git', 'Python 3.13', 'make', 'dpkg-deb', 'zstd',
                                                 'system C headers and linker'],
                      method=dict(clean='git clone --no-local; empty build directories',
                                  timing='wall seconds; tool provisioning and LOC-only expansion excluded; serial arms; no LTO',
                                  compile='exactly 100000 lines; full frontend + backend + native link; 180s total',
                                  memory='wait4 per command; peak resident bytes, maximum across pipeline phases',
                                  runtime='5 fresh processes; n=2000000; median includes process startup',
                                  loc='all physical lines including blanks/comments; frontend source only; shared harness separate',
                                  change='baseline without remainder -> final % between addition and multiplication',
                                  generated='frontend generated code plus sample emitted code; Lang expansion AST separately'))
        for name in ('clang', sys.executable):
            version = self.call([name, '--version'])
            report.setdefault('host_tools', {})[name] = Path(version['stdout']).read_text()
        for name, cmd in {
            'bison': [self.tools / 'prefix/usr/bin/bison', '--version'],
            'flex': [self.tools / 'prefix/usr/bin/flex', '--version'],
            'java': [self.tools / 'jre/bin/java', '-version'],
            'antlr': [self.tools / 'jre/bin/java', '-jar', self.tools / 'antlr-4.13.2-complete.jar'],
        }.items():
            run = self.call(cmd)
            report.setdefault('installed_tools', {})[name] = (Path(run['stdout']).read_text() + Path(run['stderr']).read_text())
        assert '23.1.5' in report['host_tools']['clang'], 'This measurement pins Clang 23.1.5'
        if self.sdk:
            report['sdk'] = json.loads((self.sdk / 'sdk.json').read_text())
            assert report['sdk']['commit'] == head, 'SDK must be built from measured HEAD'
            report['dependencies']['lang-sdk'] = ['versioned Lang SDK at measured HEAD', 'Clang 23.1.5']
        fixtures = self.base / 'fixtures'
        large = self.work / 'large.tariff'
        # Exactly 100000 physical lines, all inside one function, no huge expression stack.
        with large.open('w') as out:
            out.write('fn compute(n) {\nlet x = n;\n')
            for _ in range(99996):
                out.write('x = x + 1;\n')
            out.write('return x;\n}\n')
        assert sum(1 for _ in large.open()) == 100000
        report['large_input'] = dict(lines=100000, increments=99996, sha256=sha(large), path=str(large))
        for f in sorted(fixtures.rglob('*.tariff')):
            report['input_hashes'][str(f.relative_to(self.base))] = sha(f)
        report['source_hashes'] = {str(f.relative_to(self.base)): sha(f)
                                   for f in sorted(self.base.rglob('*')) if f.is_file()}
        report['tool_manifest'] = json.loads((self.tools / 'manifest.json').read_text())
        for arm in (*ARMS, *(('lang-sdk',) if self.sdk else ())):
            print(f'Building and measuring {arm}', flush=True)
            armroot = self.work / arm
            armroot.mkdir()
            source = self.base / ('lang' if arm == 'lang-sdk' else arm)
            row = report['arms'][arm] = dict(status='RUNNING')
            build = self.build(arm, source, armroot / 'build', build_compiler=arm == 'lang')
            sample = self.compile(arm, build, fixtures / 'benchmark.tariff', armroot / 'benchmark')
            self.expect(sample, 2000000, 6000002995045)
            # This expansion exists only for LOC accounting, after the working binary.
            # build['seconds'] and sample['seconds'] have already stopped timing.
            if arm in ('lang', 'lang-sdk'):
                expanded = armroot / 'build/reader.ast'
                compiler = self.sdk / 'bin/lang' if arm == 'lang-sdk' else self.root / 'out/lang_next'
                row['loc_expansion'] = self.call([compiler,
                                                 source / 'tariff.lang', '--emit-expanded-ast', '-o', expanded],
                                                 cwd=armroot if arm == 'lang-sdk' else None)
                build['generated'].append(expanded)
            row.update(status='PASS', clean_to_binary_seconds=build['seconds'] + sample['seconds'],
                       build_seconds=build['seconds'], sample=sample,
                       handwritten_lines=sum(len(f.read_text().splitlines()) for f in source.iterdir() if f.is_file()),
                       generated_frontend_lines=sum(len(f.read_text().splitlines()) for f in build['generated']),
                       generated_frontend_files={str(f): len(f.read_text().splitlines()) for f in build['generated']})
            times = [self.expect(sample, 2000000, 6000002995045)['seconds'] for _ in range(5)]
            row['runtime_seconds'] = times
            row['runtime_median_seconds'] = statistics.median(times)
            row['binary_bytes'] = sample['binary_bytes']
            row['diagnostics'] = {}
            for f in sorted((fixtures / 'invalid').glob('*.tariff')):
                run = self.call(build['frontend'] + [f], required=False)
                stderr = Path(run['stderr']).read_text()
                stdout = Path(run['stdout']).read_text()
                assert run['exit_code'] == 1 and stderr and not stdout, run
                row['diagnostics'][f.stem] = dict(exit_code=run['exit_code'], stdout=stdout,
                                                  stderr=stderr, log=run['stderr'],
                                                  properties=score_diagnostic(stderr, f.name, f.read_text()))
            probes = {}
            for name, n, expected in [('precedence', 0, 7), ('operators', 1, 7),
                                      ('baseline', 4, 14), ('functions', 4, 5), ('decimal', 0, -23)]:
                probes[name] = self.compile(arm, build, fixtures / (name + '.tariff'), armroot / name)
                self.expect(probes[name], n, expected)
            row['comments'] = self.comments(arm, build, fixtures, armroot / 'comments')
            # The actual earlier grammar is built, exercised, and required to reject %.
            before = self.base / 'baseline' / ('lang' if arm == 'lang-sdk' else arm)
            old = self.build(arm, before, armroot / 'before')
            previous = self.compile(arm, old, fixtures / 'baseline.tariff', armroot / 'before-native')
            self.expect(previous, 4, 14)
            old_decimal = self.compile(arm, old, fixtures / 'decimal.tariff', armroot / 'before-decimal')
            self.expect(old_decimal, 0, -23)
            rejected = self.call(old['frontend'] + [fixtures / 'precedence.tariff'], required=False)
            assert rejected['exit_code'] == 1 and Path(rejected['stderr']).read_text(), rejected
            row['baseline_comments'] = self.comments(arm, old, fixtures, armroot / 'before-comments')
            changes, added, removed = frontend_diff(before, source)
            patch = armroot / 'operator-change.diff'
            patch.write_text(changes)
            row['operator_change'] = dict(added=added, removed=removed, lines_touched=added + removed,
                                          patch=str(patch), diff=changes, baseline=previous, probes=probes,
                                          baseline_decimal=old_decimal,
                                          baseline_rejects_remainder=rejected)
            if not smoke:
                row['large_compile'] = self.compile(arm, build, large, armroot / 'large')
                if row['large_compile']['status'] == 'PASS':
                    row['large_run'] = self.expect(row['large_compile'], 4, 100000)
                    row['large_lines_per_second'] = 100000 / row['large_compile']['seconds']
                else:
                    # A reproducible product limit is a measured loss, not a
                    # successful compilation. Preserve the failed command.
                    failure = row['large_compile'].get('lowering', {})
                    detail = Path(failure['stderr']).read_text() if failure else ''
                    if arm in ('lang', 'lang-sdk') and failure.get('exit_code') == 1 and '(code ast-nodes)' in detail:
                        row['status'] = 'MEASURED_LIMIT'
                        row['large_failure'] = detail
                    else:
                        row['status'] = 'UNEXPECTED_FAILURE'
            self.report.write_text(json.dumps(report, indent=2) + '\n')
        report['shared_harness_lines'] = len((self.base / 'harness.c').read_text().splitlines())
        metrics = dict(handwritten_lines=False, generated_frontend_lines=False,
                       clean_to_binary_seconds=False, runtime_median_seconds=False, binary_bytes=False)
        if not smoke:
            metrics['large_lines_per_second'] = True
        report['winners'] = {}
        for metric, higher in metrics.items():
            values = {arm: row[metric] for arm, row in report['arms'].items() if metric in row}
            best = (max if higher else min)(values.values())
            report['winners'][metric] = [arm for arm, value in values.items() if value == best]
        report['winners']['dependencies'] = ['lang-sdk'] if self.sdk else ['lang']
        report['diagnostics_scores'] = {
            arm: dict(total=sum(sum(d['properties'].values()) for d in row['diagnostics'].values()),
                      maximum=25) for arm, row in report['arms'].items()}
        report['status'] = 'PASS' if all(r['status'] in ('PASS', 'MEASURED_LIMIT') for r in report['arms'].values()) else 'FAIL'
        report['status_meaning'] = 'PASS means all measurements executed and small native programs agreed; inspect large_compile.status for scale success.'
        self.report.write_text(json.dumps(report, indent=2) + '\n')
        if not smoke:
            scale = dict(version=1, head=head, lines=100000, input=report['large_input'],
                         historical_seconds=dict(bison=0.635, antlr=10.465), arms={})
            for arm, row in report['arms'].items():
                result = row['large_compile']
                phases = {'frontend': result['frontend'], 'native_link': result.get('native')}
                if arm == 'lang':
                    phases['backend'] = result.get('lowering')
                scale['arms'][arm] = dict(status=result['status'], total_seconds=result['seconds'],
                    lines_per_second=row.get('large_lines_per_second'), peak_rss_bytes=result.get('peak_rss_bytes'),
                    phases={k: dict(seconds=v['seconds'], peak_rss_bytes=v['peak_rss_bytes'])
                            for k, v in phases.items() if v}, verified_run=row.get('large_run'))
            (self.report.parent / 'scale.json').write_text(json.dumps(scale, indent=2) + '\n')
        print(json.dumps(dict(report=str(self.report), status=report['status'], winners=report['winners'])))
        return 0 if report['status'] == 'PASS' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--sdk', type=Path, help='extracted SDK; provision before timing')
    args = parser.parse_args()
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO).strip(), 'Commit the candidate first'
    assert not any(k.startswith('LANG_HOST_MAX_') for k in os.environ), 'Measure default host limits'
    (args.report.resolve().parent.parent / 'scratch').mkdir(exist_ok=True)
    return Experiment(args.tools, args.report, args.sdk).run(args.smoke)


if __name__ == '__main__':
    raise SystemExit(main())
