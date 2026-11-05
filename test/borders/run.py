#!/usr/bin/env python3
"""Measure reader/feature/target borders with small, independently runnable probes.

Filtered runs never update the published grid. Use --output for fragment evidence;
only an unfiltered run writes borders.json, bug reproducers, and docs/BORDERS.md.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
READERS = 'lang minipy minilisp c forth flow lox lua tiny calc'.split()
FEATURES = ('integers floats strings functions closures structs arrays control_flow '
            'recursion effects cross_reader_call error_location').split()
TARGETS = ['llvm', 'llvm-wasm', 'wasm']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def symptom(cell):
    """Compare a failure while ignoring its input file's spelling."""
    steps = cell.get('steps', [])
    last = steps[-1] if steps else {}
    fixture = cell['fixture']
    if Path(fixture).is_absolute():
        fixture = '<scratch>/' + Path(fixture).name
    def clean(text):
        text = text.replace(fixture, '<fixture>')
        return re.sub(r'<fixture>:\d+:\d+', '<fixture>:L:C', text)
    return (cell['status'], cell.get('phase'), cell.get('exit_code'),
            clean(last.get('stdout', '')), clean(last.get('stderr', '')))


class Probe:
    def __init__(self, compiler, scratch):
        self.compiler = compiler
        self.scratch = Path(scratch)
        self.steps = []

    def clean(self, text):
        return text.replace(str(self.scratch), '<scratch>').replace(str(ROOT) + '/', '')

    def run(self, command, env):
        try:
            p = subprocess.run(command, env=env, capture_output=True, text=True,
                               errors='replace', timeout=30)
            code, stdout, stderr = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = 124, '', 'probe timed out after 30 seconds'
        result = dict(command=[self.clean(str(s)) for s in command], exit_code=code,
                      stdout=self.clean(stdout), stderr=self.clean(stderr))
        self.steps.append(result)
        return code, result['stdout'], result['stderr']

    def measure(self, reader, feature, target, spec, fixture=None):
        self.steps = []
        fixture = fixture or spec['fixture']
        cell = dict(reader=reader, feature=feature, target=target, fixture=fixture,
                    fixture_sha256=digest(fixture), expected_exit=spec['expected_exit'],
                    expected_stdout=spec['expected_stdout'], case_sha256=digest(spec['fixture']))
        if 'reason' in spec:
            return dict(cell, status='not-applicable', reason=spec['reason'])
        output = self.scratch / ('program.wasm' if target == 'wasm' else 'program.ll')
        backend = 'wasm' if target == 'wasm' else 'llvm'
        env = dict(os.environ, LANGBE=backend, LANGOS='linux' if target == 'llvm' else 'wasm',
                   LANG_CACHE=str(self.scratch / 'cache'), LANG_BORDERS_TRAPS='1')
        code, stdout, stderr = self.run([self.compiler, fixture, '-o', str(output)], env)
        phase = 'compile'
        detail = stdout + stderr
        if 'diagnostic' in spec:
            # This is an intentionally invalid input. Its oracle is a precise
            # guest-source location, rather than a successful target execution.
            cell['diagnostic'] = spec['diagnostic']
            status = 'supported' if code > 0 and re.search(spec['diagnostic'], detail) else 'wrong'
        elif code:
            status = 'crash' if code < 0 or code == 124 else 'rejected'
        else:
            if target == 'llvm':
                binary = str(self.scratch / 'program')
                command = ['clang', '-O0', str(output), '-o', binary]
            elif target == 'llvm-wasm':
                binary = str(self.scratch / 'program.wasm')
                command = ['clang', '--target=wasm32-unknown-unknown', '-nostdlib',
                           '-Wl,--no-entry', '-Wl,--export-all', '-Wl,--allow-undefined',
                           '-Wl,-z,stack-size=8388608', str(output), '-o', binary]
            else:
                command = None
                binary = str(output)
            if command:
                phase = 'link'
                code, stdout, stderr = self.run(command, env)
                detail = stdout + stderr
            if code:
                status = 'crash' if code < 0 or code == 124 else 'rejected'
            else:
                phase = 'run'
                command = [binary] if target == 'llvm' else ['node', 'test/wasm_host.js', binary]
                code, stdout, stderr = self.run(command, env)
                detail = stdout + stderr
                if code == spec['expected_exit'] and stdout == spec['expected_stdout'] and not stderr:
                    status = 'supported'
                elif code < 0 or code == 124 or (code == 139 and 'borders: wasm trap' in stderr):
                    status = 'crash'
                else:
                    status = 'wrong'
        return dict(cell, status=status, phase=phase, exit_code=code, detail=detail, steps=list(self.steps))


def check_missing_reader(probe):
    """Keep the previous grid's absent-reader/location regression check."""
    probe.steps = []
    code, stdout, stderr = probe.run(
        [probe.compiler, 'read', 'example/c/c.lang', 'test/borders/missing.zig'],
        dict(os.environ, LANG_CACHE=str(probe.scratch / 'cache')))
    detail = stdout + stderr
    if code == 0 or 'test/borders/missing.zig:1:1: error:' not in detail or "reader 'zig' not found" not in detail:
        raise SystemExit('Zig missing-reader check failed: ' + detail)
    return list(probe.steps)


def main():
    os.chdir(ROOT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reader', choices=READERS)
    parser.add_argument('--target', choices=TARGETS)
    parser.add_argument('--feature', choices=FEATURES)
    parser.add_argument('--output', type=Path, help='write fragment measurements here')
    parser.add_argument('--verify', action='store_true', help='compare fragment outcomes with the published grid')
    parser.add_argument('--minimality', action='store_true', help='test wrong/crash fixture include deletions (requires filters)')
    parser.add_argument('--prepare-bugs', action='store_true', help='minimize and save bug fixtures for one filtered reader')
    parser.add_argument('--check-missing-reader', action='store_true', help='run only the inherited absent-reader regression')
    args = parser.parse_args()
    filtered = any([args.reader, args.target, args.feature])
    if args.minimality and not filtered:
        parser.error('--minimality requires a reader, target, or feature filter')
    if args.prepare_bugs and not args.reader:
        parser.error('--prepare-bugs requires --reader')
    specs = json.loads(Path('test/borders/probes.json').read_text())
    published = {(c['reader'], c['feature'], c['target']): c for c in json.loads(Path('borders.json').read_text())['cells']}
    compiler = str(Path(os.environ.get('COMPILER', 'out/lang_next')).resolve())
    if args.check_missing_reader:
        with tempfile.TemporaryDirectory(prefix='borders-') as temp:
            check_missing_reader(Probe(compiler, temp))
        print('Zig missing-reader location check passed')
        return
    cells = []
    missing_reader = None
    minimality_path = Path('test/borders/bugs/minimality.json')
    minimality = json.loads(minimality_path.read_text()) if minimality_path.exists() else {}
    # TMPDIR can place compiler artifacts and reader caches outside the checkout.
    with tempfile.TemporaryDirectory(prefix='borders-') as temp:
        probe = Probe(compiler, temp)
        if not filtered:
            missing_reader = check_missing_reader(probe)
        for reader in ([args.reader] if args.reader else READERS):
            for feature in ([args.feature] if args.feature else FEATURES):
                for target in ([args.target] if args.target else TARGETS):
                    spec = specs[f'{reader}/{feature}']
                    cell = probe.measure(reader, feature, target, spec)
                    if cell['status'] in ('wrong', 'crash'):
                        bug = f'test/borders/bugs/{reader}_{feature}_{target}.lang'
                        if args.prepare_bugs:
                            lines = Path(spec['fixture']).read_text().splitlines(True)
                            # Reader declarations defining the feature boundary are
                            # protected; deleting one would change which language
                            # (or pair of languages) the reproducer exercises.
                            protected = {line for line in lines if line.startswith('include ') and
                                         line.rstrip().endswith(f'/{reader}.lang"')}
                            if feature == 'cross_reader_call':
                                protected |= {line for line in lines if line.startswith('include "example/') and 'runtime' not in line}
                            reductions = []
                            changed = True
                            while changed:
                                changed = False
                                for i, line in enumerate(lines):
                                    if not line.startswith('include ') or line in protected:
                                        continue
                                    trial = Path(temp) / 'reduced.lang'
                                    trial.write_text(''.join(lines[:i] + lines[i+1:]))
                                    result = probe.measure(reader, feature, target, spec, str(trial))
                                    same = symptom(result) == symptom(cell)
                                    reductions.append(dict(removed=line.strip(), reproduces=same, result=result))
                                    if same:
                                        lines.pop(i)
                                        cell = result
                                        changed = True
                                        break
                            Path(bug).write_text(''.join(lines))
                            cell = probe.measure(reader, feature, target, spec, bug)
                            cell['include_deletions'] = reductions
                            minimality[bug] = dict(sha256=digest(bug),
                                protected_includes=sorted(s.strip() for s in protected),
                                final_includes=[s.strip() for s in lines if s.startswith('include ')],
                                reductions=[dict(removed=r['removed'], reproduces=r['reproduces'],
                                                 status=r['result']['status'], phase=r['result'].get('phase')) for r in reductions])
                        elif not filtered or args.minimality:
                            if not Path(bug).exists() or bug not in minimality or minimality[bug]['sha256'] != digest(bug):
                                raise SystemExit(f'prepare this reproducer with --reader {reader} --prepare-bugs: {bug}')
                            reduced = probe.measure(reader, feature, target, spec, bug)
                            if symptom(reduced) != symptom(cell):
                                raise SystemExit(f'reproducer changed the failure: {bug}')
                            cell = reduced
                            if args.minimality:
                                record = minimality[bug]
                                cell['include_deletions'] = []
                                lines = Path(bug).read_text().splitlines(True)
                                for i, line in enumerate(lines):
                                    if not line.startswith('include ') or line.strip() in record['protected_includes']:
                                        continue
                                    trial = Path(temp) / 'reduced.lang'
                                    trial.write_text(''.join(lines[:i] + lines[i+1:]))
                                    result = probe.measure(reader, feature, target, spec, str(trial))
                                    same = symptom(result) == symptom(cell)
                                    cell['include_deletions'].append(dict(removed=line.strip(), reproduces=same, result=result))
                                    if same:
                                        raise SystemExit(f'nonminimal runtime include in {bug}: {line.strip()}')
                    cells.append(cell)
                    print(f'{reader}/{feature}/{target}: {cell["status"]}', flush=True)
    data = {'schema': 2, 'compiler_sha256': digest(compiler), 'cells': cells,
            'totals': dict(sorted(Counter(c['status'] for c in cells).items()))}
    if missing_reader is not None:
        data['missing_reader'] = missing_reader
    if args.output:
        args.output.write_text(json.dumps(data, indent=2) + '\n')
    if args.prepare_bugs:
        minimality_path.write_text(json.dumps(minimality, indent=2) + '\n')
    if not filtered and not args.verify:
        Path('borders.json').write_text(json.dumps(data, indent=2) + '\n')
        subprocess.run(['python3', '-B', 'test/borders/render.py', '--write'], check=True)
    if args.verify:
        for cell in cells:
            old = published[(cell['reader'], cell['feature'], cell['target'])]
            for key in ('status', 'exit_code', 'expected_exit', 'expected_stdout'):
                if old.get(key) != cell.get(key):
                    raise SystemExit(f'changed {key}: {cell["reader"]}/{cell["feature"]}/{cell["target"]}: {old.get(key)} -> {cell.get(key)}')
    print('Totals: ' + ', '.join(f'{k}: {v}' for k, v in data['totals'].items()))


if __name__ == '__main__':
    main()
