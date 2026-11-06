#!/usr/bin/env python3
"""Project fixture host. Language semantics stay in the selected reader/runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import time
import uuid

PHASES = ['reader', 'validation', 'llvm', 'object', 'link']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def fields(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= value.keys() <= set(required) | set(optional),
            'invalid fixture fields: expected ' + ', '.join(required))


def load_suite(path, selected):
    suite = json.loads(path.read_text())
    fields(suite, ['version', 'fixtures'])
    require(type(suite['version']) is int and suite['version'] == 1, 'unsupported fixture version')
    require(isinstance(suite['fixtures'], list) and suite['fixtures'], 'fixtures must be a nonempty list')
    names = set()
    for case in suite['fixtures']:
        fields(case, ['name', 'source'], ['runs', 'diagnostic'])
        name = case['name']
        require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_-]+', name), 'invalid fixture name')
        require(name not in names, 'duplicate fixture name: ' + name)
        names.add(name)
        require(isinstance(case['source'], str) and case['source'], name + ': source must be a path')
        require((path.parent / case['source']).is_file(), name + ': missing source')
        require(('runs' in case) != ('diagnostic' in case), name + ': choose runs or diagnostic')
        if 'runs' in case:
            require(isinstance(case['runs'], list) and len(case['runs']) >= 2,
                    name + ': positive source needs at least two runtime inputs')
            for run in case['runs']:
                fields(run, ['args', 'stdout', 'stderr', 'exit'])
                require(isinstance(run['args'], list) and all(isinstance(a, str) and '\0' not in a for a in run['args']),
                        name + ': args must be strings')
                require(isinstance(run['stdout'], str) and isinstance(run['stderr'], str), name + ': output must be text')
                require(type(run['exit']) is int and 0 <= run['exit'] <= 255, name + ': invalid runtime exit')
            require(len({tuple(r['args']) for r in case['runs']}) >= 2, name + ': runtime inputs must differ')
        else:
            diag = case['diagnostic']
            fields(diag, ['label', 'line', 'column', 'message_contains'])
            require(isinstance(diag['label'], str) and diag['label'] and
                    isinstance(diag['message_contains'], str) and diag['message_contains'], name + ': empty diagnostic assertion')
            require(all(type(diag[k]) is int and diag[k] > 0 for k in ['line', 'column']), name + ': invalid diagnostic location')
    if selected is not None:
        require(selected in names, 'unknown fixture: ' + selected)
        return [c for c in suite['fixtures'] if c['name'] == selected]
    return suite['fixtures']


class Runner:
    def __init__(self, evidence, env):
        self.evidence, self.env, self.commands = evidence, env, []

    def run(self, command, name):
        prefix = self.evidence / f'{len(self.commands) + 1:03d}-{name}'
        start = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        try:
            result = subprocess.run(command, env=self.env, capture_output=True, timeout=120)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr = 124, error.stdout or b'', (error.stderr or b'') + b'\nfixture command timed out\n'
        except OSError as error:
            code, stdout, stderr = 127, b'', str(error).encode()
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        prefix.with_suffix('.stdout').write_bytes(stdout)
        prefix.with_suffix('.stderr').write_bytes(stderr)
        phase_rows = re.findall(rb'^Native phase ([0-4]) nanoseconds (\d+) exit (-?\d+)$', stderr, re.M)
        phases = {PHASES[int(stage)]: int(nanos) / 1e9 for stage, nanos, code in phase_rows}
        phase_exits = {PHASES[int(stage)]: int(code) for stage, nanos, code in phase_rows}
        row = {'command': command, 'cwd': os.getcwd(), 'exit': code,
               'stdout': prefix.name + '.stdout', 'stderr': prefix.name + '.stderr',
               'wall_seconds': time.monotonic() - start,
               'cpu_user_seconds': after.ru_utime - before.ru_utime,
               'cpu_system_seconds': after.ru_stime - before.ru_stime,
               'phase_seconds': phases, 'phase_exits': phase_exits}
        self.commands.append(row)
        write_json(self.evidence / 'commands.json', self.commands)
        return code, stdout, stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', required=True)
    parser.add_argument('--input-identity', required=True)
    parser.add_argument('--reader', required=True)
    parser.add_argument('--runtime', action='append', default=[])
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--fixture')
    parser.add_argument('--fixtures', type=Path)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    suite_path = (args.fixtures or args.project.parent / 'tests.json').resolve()
    evidence = (args.evidence or args.project.parent / 'build' / ('tests-' + uuid.uuid4().hex)).resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    print('Evidence: ' + str(evidence), flush=True)
    results = []
    runner = None
    try:
        cases = load_suite(suite_path, args.fixture)
        compiler = identity(args.compiler)
        tool_name = os.environ.get('LANG_CLANG') or 'clang'
        tool_path = shutil.which(tool_name)
        require(tool_path is not None, 'native toolchain not found: ' + tool_name)
        tool = identity(tool_path)
        linker = shutil.which('ld')
        env = dict(os.environ, LANG_TEST_TIMINGS='1', LANG_CLANG=tool['path'])
        runner = Runner(evidence, env)
        sources = {case['source']: identity(suite_path.parent / case['source']) for case in cases}
        original = {'compiler': compiler, 'project': identity(args.project), 'project_inputs': args.input_identity,
                    'reader': identity(args.reader), 'runtime': [identity(p) for p in args.runtime],
                    'fixtures': identity(suite_path), 'sources': sources,
                    'toolchain': tool, 'linker': identity(linker) if linker else None,
                    'host': identity(__file__), 'python': identity(sys.executable),
                    'environment': {k: env.get(k) for k in ['JOBS', 'LANGBE', 'LANGOS', 'LANG_ROOT', 'LANG_CACHE', 'LANG_CLANG']}}
        write_json(evidence / 'identity.json', original)
        code, _, _ = runner.run([tool['path'], '--version'], 'toolchain-version')
        require(code == 0, 'native toolchain could not report its version')
        for case in cases:
            name = case['name']
            source = sources[case['source']]['path']
            output = evidence / (name + ('.ast' if 'diagnostic' in case else '.native'))
            command = [compiler['path'], 'build', '--project', str(args.project.resolve()), source, '-o', str(output)]
            if 'diagnostic' in case:
                command += ['--emit=ast']
            code, stdout, stderr = runner.run(command, name + '-build')
            try:
                if 'diagnostic' in case:
                    # Only a rejected reader with a located diagnostic satisfies a negative.
                    # A missing tool, manifest/LLVM/link error, signal, or timeout cannot pass.
                    require(code == 1 and b'native build reader failed' in stderr and not output.exists(),
                            'expected reader rejection with exit 1')
                    diag = case['diagnostic']
                    pattern = (r'^' + re.escape(diag['label']) + r':(\d+):(\d+): (.*)$').encode()
                    diagnostics = [{'label': diag['label'], 'line': int(line), 'column': int(column),
                                    'message': message.decode(errors='replace')}
                                   for line, column, message in re.findall(pattern, stderr, re.M)]
                    write_json(evidence / (name + '-diagnostics.json'), {'source': source, 'diagnostics': diagnostics})
                    require(any(d['line'] == diag['line'] and d['column'] == diag['column'] and
                                diag['message_contains'] in d['message'] for d in diagnostics),
                            'structured diagnostic mismatch: ' + json.dumps(diag))
                else:
                    require(code == 0 and output.is_file() and output.read_bytes().startswith(b'\x7fELF'),
                            'native build failed before successful publication')
                    require(set(runner.commands[-1]['phase_seconds']) == set(PHASES) and
                            all(code == 0 for code in runner.commands[-1]['phase_exits'].values()),
                            'missing successful native phase timings')
                    for index, expected in enumerate(case['runs']):
                        actual = runner.run([str(output), *expected['args']], name + '-run-' + str(index))
                        require(actual == (expected['exit'], expected['stdout'].encode(), expected['stderr'].encode()),
                                f'args {expected["args"]}: expected {expected}, got exit={actual[0]} stdout={actual[1]!r} stderr={actual[2]!r}')
                results.append({'name': name, 'pass': True})
                print('PASS ' + name, flush=True)
            except ValueError as error:
                results.append({'name': name, 'pass': False, 'error': str(error)})
                print('FAIL ' + name + ': ' + str(error), file=sys.stderr, flush=True)
        # Do not silently accept changes to the compiler or authored inputs during execution.
        for record in [compiler, original['project'], original['reader'], *original['runtime'],
                       original['fixtures'], *sources.values(), tool]:
            require(identity(record['path']) == record, 'input changed during test: ' + record['path'])
        passed = all(row['pass'] for row in results)
        write_json(evidence / 'result.json', {'pass': passed, 'fixtures': results, 'compiler_sha256': compiler['sha256']})
        return 0 if passed else 1
    except (ValueError, OSError, KeyError, TypeError) as error:
        write_json(evidence / 'result.json', {'pass': False, 'error': str(error), 'fixtures': results})
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
