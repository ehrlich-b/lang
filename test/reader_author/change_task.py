#!/usr/bin/env python3
"""Replay one preregistered Harbor edit against frozen native trial arms."""
import argparse
import ctypes
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile

BASE = 'e148de1e1a3bb1a229f3a8369e41e4b0241783e3'
INPUT_HEAD = '209e4ca1e12a643102e37b58b6e43fe7ce4c5eaf'
MANIFEST = '0be69a0effd5dab92a1122471a382d0e32fe49b495ee298e36c3e370bef9702e'
REGISTERED = {
    'CHANGE.md': '0811c049977d94490c5c86fe11eecd52bc22c910d60edba1017b06d9c53341e9',
    'fixtures.json': '6ee89ffc8633a0f55977ca702509a5e3095fe813ed9dca9af7b87c3488d1d7ea',
    'fixtures/boolean-eof.conf': '645d57546ee4f6a2ba0ece32d93bb1f1dca4e4f4e990b01647e40a1ad61cbaa3',
    'fixtures/integer.conf': 'd9aaf1327c7d494592be860a42ca2dfb12fa99d1c955fbc8c997cc7368f64962',
    'fixtures/missing-comment.conf': 'a8448d57350022bd78bd4d4f446eaac71b474bcaa41103bc87f218a1ea68ec1c',
    'fixtures/string.conf': 'd55724d2f5ba731a2ee2fd80fd7201a808da55da0341995adfa4900cf6e5c4da',
}
SOURCES = {'lang': ['harbor.lang'], 'bison': ['harbor.y', 'harbor.l', 'harbor.c', 'harbor.h'],
           'antlr': ['Harbor.g4', 'main.cpp']}
EDITS = {
    'lang/harbor.lang': [
        ("    harbor_assignment = key:symbol '=' value:harbor_value <eol>",
         "    harbor_assignment = key:symbol '=' value:harbor_value harbor_inline_comment? <eol>\n"
         "    harbor_inline_comment = ';' string")],
    'bison/harbor.y': [
        ("| identifier '=' value EOL {", "| identifier '=' value inline_comment EOL {"),
        ('identifier:\n', "inline_comment:\n    %empty\n  | ';' STRING { free($2); }\n;\nidentifier:\n")],
    'bison/harbor.l': [
        ('"["|"]"|"="', '"["|"]"|"="|";"')],
    'antlr/Harbor.g4': [
        ('assignment : identifier EQUAL value ;',
         'assignment : identifier EQUAL value inlineComment? ;\ninlineComment : SEMICOLON STRING ;'),
        ("EQUAL : '=' ;", "EQUAL : '=' ;\nSEMICOLON : ';' ;")],
}
CASES = ['old-sample', 'new-feature', 'missing-feature-value', 'old-invalid',
         'changed-lines', 'native-execution']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def edited(name, original):
    for before, after in EDITS.get(name, []):
        assert original.count(before) == 1, ('patch context', name, before)
        original = original.replace(before, after)
    return original


def patch(name, original, changed):
    return ''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True),
                                      fromfile='baseline/' + name, tofile='edited/' + name))


def inputs_ok(repo, inputs):
    assert os.geteuid() != 0, 'unprivileged execution required'
    assert socket.gethostname() != 'forge', 'compiler replay requires a suitable host'
    assert git(inputs, 'rev-parse', 'HEAD') == INPUT_HEAD
    assert sha(inputs / 'MANIFEST.json') == MANIFEST
    rows = json.loads((inputs / 'MANIFEST.json').read_text())
    for row in rows:
        assert sha(inputs / row['path']) == row['sha256'], row['path']
    assert git(repo, 'merge-base', BASE, 'HEAD') == BASE
    assert git(repo, 'cat-file', '-t', BASE + ':examples/dsl-compare/README.md') == 'blob'
    return rows


def parser_tools(repo):
    """Require the complete local bundle before starting any native build."""
    tools = repo.parent / 'tools'
    required = ['prefix/usr/bin/bison', 'prefix/usr/bin/flex', 'prefix/usr/bin/m4',
                'prefix/usr/share/bison/skeletons/yacc.c', 'jre/bin/java',
                'antlr-4.13.2-complete.jar', 'runtime/lib/libantlr4-runtime.a',
                'runtime/include/antlr4-runtime/antlr4-runtime.h', 'manifest.json']
    missing = [name for name in required if not (tools / name).is_file()]
    assert not missing, ('missing parser tools', missing,
                         'run: nice -n 10 python3 examples/dsl-compare/install.py '
                         '--harbor --tools ../tools')
    for name in ['prefix/usr/bin/bison', 'prefix/usr/bin/flex', 'prefix/usr/bin/m4', 'jre/bin/java']:
        assert os.access(tools / name, os.X_OK), ('not executable', name)
    return tools, {name: sha(tools / name) for name in required}


def validate(base, repo, inputs):
    """Check actual retained outputs and patch identities, not reported success flags."""
    rows = inputs_ok(repo, inputs)
    for name, digest in REGISTERED.items():
        assert sha(base / name) == digest, ('preregistration', name)
    assert json.loads((base / 'preregistration.json').read_text())['files'] == REGISTERED
    manifest = {row['path']: row['sha256'] for row in rows}
    expected_patches = {}
    for arm, names in SOURCES.items():
        for name in names:
            key = arm + '/' + name
            old, new = base / 'baseline' / key, base / 'edited' / key
            assert sha(old) == manifest[key], ('changed input', key)
            assert new.read_text() == edited(key, old.read_text()), ('unexpected edit', key)
            if key in EDITS:
                expected_patches[key] = {'before': sha(old), 'after': sha(new),
                                         'patch': patch(key, old.read_text(), new.read_text())}
    assert json.loads((base / 'patches.json').read_text()) == expected_patches
    result = json.loads((base / 'result.json').read_text())
    assert result['head'] == git(repo, 'rev-parse', 'HEAD') and result['kind'] == 'change-task'
    assert set(result['cases']) == set(CASES)
    for case in result['cases'].values():
        assert case['passed'] is True and case['command'] and case['exit_code'] == 0
        assert case['assertion'] and case['files']
        for name, digest in case['files'].items():
            path = (base / name).resolve()
            assert path.is_relative_to(base.resolve()) and sha(path) == digest, name
    records = [json.loads(line) for line in (base / 'commands.jsonl').read_text().splitlines()]
    fixtures = json.loads((base / 'fixtures.json').read_text())
    by_id = {}
    for record in records:
        assert record['id'] not in by_id
        by_id[record['id']] = record
        assert record['command'] == shlex.join(record['argv'])
        for stream in ['stdout', 'stderr']:
            p = base / record[stream + '_file']
            assert sha(p) == record[stream + '_sha256']
            assert p.read_text() == record[stream]
        assert record['input_hashes'] and record['cwd']
        if record['stage'] == 'build':
            assert record['exit_code'] == 0, record
    for arm in SOURCES:
        sample = json.loads((inputs / arm / 'trial-results.json').read_text())
        # Trial formats differ, but their original literal sample output is retained.
        if isinstance(sample, dict):
            sample = sample.get('cases', sample.get('results'))
        expected = next(r['stdout'] for r in sample if Path(r.get('file', r.get('name', ''))).name == 'sample.conf')
        for version in ['baseline', 'edited']:
            for name in ['sample.conf', 'missing-equals.conf', *fixtures]:
                r = by_id[arm + '/' + version + '/' + name]
                if name == 'sample.conf':
                    assert (r['exit_code'], r['stdout'], r['stderr']) == (0, expected, ''), r
                elif name == 'missing-equals.conf' or name == 'missing-comment.conf' or version == 'baseline':
                    assert r['exit_code'] == 1 and r['stdout'] == '', r
                    assert re.search(r':\d+:\d+:', r['stderr']), r
                else:
                    assert (r['exit_code'], r['stdout'], r['stderr']) == (0, fixtures[name][arm], ''), r
            before = by_id[arm + '/baseline/missing-equals.conf']
            after = by_id[arm + '/edited/missing-equals.conf']
            assert all(before[k] == after[k] for k in ['exit_code', 'stdout', 'stderr'])
    assert result['native_artifacts'] and len(result['native_artifacts']) == 6
    assert all(a['magic'] == '7f454c46' and len(a['sha256']) == 64 for a in result['native_artifacts'])


def replay(base, repo, inputs):
    inputs_ok(repo, inputs)
    tools, tool_hashes = parser_tools(repo)
    for name, digest in REGISTERED.items():
        assert sha(base / name) == digest, name
    workspace = repo.parent
    scratch = workspace / 'scratch'
    scratch.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='harbor-change-', dir=scratch))
    logs = base / 'runs' / work.name
    logs.mkdir(parents=True)
    write_json(base / 'toolchain.json', {'files': tool_hashes,
               'manifest': json.loads((tools / 'manifest.json').read_text())})
    env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LC_ALL='C',
               TMPDIR=str(work), LANG_CACHE=str(work / 'cache'),
               PATH=str(tools / 'prefix/usr/bin') + ':' + os.environ['PATH'],
               BISON_PKGDATADIR=str(tools / 'prefix/usr/share/bison'),
               M4=str(tools / 'prefix/usr/bin/m4'))
    records, artifacts = [], []
    patches = {}
    for version in ['baseline', 'edited']:
        for arm, names in SOURCES.items():
            for name in names:
                key = arm + '/' + name
                original = (inputs / key).read_text()
                changed = edited(key, original) if version == 'edited' else original
                dest = base / version / key
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(changed)
                if version == 'edited' and key in EDITS:
                    patches[key] = {'before': sha(inputs / key), 'after': sha(dest),
                                    'patch': patch(key, original, changed)}
    write_json(base / 'patches.json', patches)

    def call(identifier, argv, cwd, hashes, stage='build'):
        argv = ['nice', '-n', '10', *map(str, argv)]
        p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=180)
        n = len(records)
        record = {'id': identifier, 'stage': stage, 'argv': argv, 'command': shlex.join(argv),
                  'cwd': str(cwd), 'exit_code': p.returncode, 'input_hashes': hashes}
        for stream, value in [('stdout', p.stdout), ('stderr', p.stderr)]:
            dest = logs / (str(n) + '.' + stream)
            dest.write_bytes(value)
            record.update({stream: value.decode(), stream + '_file': str(dest.relative_to(base)),
                           stream + '_sha256': sha(dest)})
        records.append(record)
        with (base / 'commands.jsonl').open('w') as f:
            for r in records:
                f.write(json.dumps(r) + '\n')
        if stage == 'build':
            assert p.returncode == 0, record
        return record

    # Use the exact frozen SDK: this is an engineering replay, not an author trial.
    archive = inputs / 'lang/lang-0.1.0+e148de1e1a3b-x86_64-linux.tar.xz'
    with tarfile.open(archive) as t:
        t.extractall(work / 'sdk', filter='data')
    sdk = next((work / 'sdk').glob('lang-*'))
    assert json.loads((sdk / 'sdk.json').read_text())['commit'] == BASE
    for name, row in json.loads((sdk / 'sdk.json').read_text())['files'].items():
        assert sha(sdk / name) == row['sha256']
    for arm, names in SOURCES.items():
        for version in ['baseline', 'edited']:
            src = base / version / arm
            build = work / version / arm
            build.mkdir(parents=True)
            hashes = {str(p): sha(p) for p in [*(src / n for n in names), archive]}
            binary = build / 'harbor-config'
            prefix = arm + '/' + version + '/build/'
            if arm == 'lang':
                call(prefix + 'llvm', [sdk / 'bin/lang', src / 'harbor.lang', '-o', build / 'harbor.ll'], work, hashes)
                call(prefix + 'link', ['clang', '-O2', build / 'harbor.ll', '-o', binary], work,
                     {str(build / 'harbor.ll'): sha(build / 'harbor.ll')})
            elif arm == 'bison':
                call(prefix + 'parser', ['bison', '-Wall', '-Werror', '--defines=' + str(build / 'harbor.tab.h'), '-o', build / 'harbor.tab.c', src / 'harbor.y'], build, hashes)
                call(prefix + 'scanner', ['flex', '-o', build / 'harbor.lex.c', src / 'harbor.l'], build, hashes)
                call(prefix + 'link', ['clang', '-std=c11', '-D_POSIX_C_SOURCE=200809L', '-Wall', '-Wextra', '-Werror',
                                      '-O2', '-I' + str(src), '-I' + str(build), src / 'harbor.c', build / 'harbor.tab.c',
                                      build / 'harbor.lex.c', '-o', binary], build,
                     {str(p): sha(p) for p in [src / 'harbor.c', src / 'harbor.h', build / 'harbor.tab.c', build / 'harbor.lex.c']})
            else:
                java, jar = tools / 'jre/bin/java', tools / 'antlr-4.13.2-complete.jar'
                runtime = tools / 'runtime'
                call(prefix + 'parser', [java, '-Djava.io.tmpdir=' + str(work), '-jar', jar, '-Dlanguage=Cpp',
                                        '-no-listener', '-no-visitor', '-Werror', '-Xexact-output-dir', '-o', build, src / 'Harbor.g4'],
                     build, dict(hashes, **{str(jar): sha(jar)}))
                call(prefix + 'link', ['clang++', '-std=c++17', '-O2', '-s', '-I' + str(runtime / 'include/antlr4-runtime'),
                                      '-I' + str(build), src / 'main.cpp', build / 'HarborLexer.cpp', build / 'HarborParser.cpp',
                                      runtime / 'lib/libantlr4-runtime.a', '-pthread', '-o', binary], build,
                     {str(p): sha(p) for p in [src / 'main.cpp', build / 'HarborLexer.cpp', build / 'HarborParser.cpp', runtime / 'lib/libantlr4-runtime.a']})
            assert binary.read_bytes()[:4] == b'\x7fELF'
            artifacts.append({'arm': arm, 'version': version, 'path': str(binary), 'sha256': sha(binary),
                              'magic': binary.read_bytes()[:4].hex(), 'bytes': binary.stat().st_size})
            for source in [inputs / arm / 'sample.conf', inputs / arm / 'fixtures/missing-equals.conf',
                           *sorted((base / 'fixtures').glob('*.conf'))]:
                call(arm + '/' + version + '/' + source.name, [binary, source], work,
                     {str(binary): sha(binary), str(source): sha(source)}, 'native')
    files = [base / 'commands.jsonl', base / 'patches.json', base / 'preregistration.json',
             base / 'toolchain.json',
             *(base / name for name in REGISTERED), *sorted(logs.iterdir()),
             *(base / version / arm / name for version in ['baseline', 'edited']
               for arm, names in SOURCES.items() for name in names)]
    bindings = {str(p.relative_to(base)): sha(p) for p in files}
    command = shlex.join([sys.executable, '-B', str(Path(__file__).resolve()), *sys.argv[1:]])
    assertions = {
        'old-sample': 'Both versions reproduce each frozen sample stdout literally.',
        'new-feature': 'Only edited arms accept all three valid registered comment suffixes with literal stdout.',
        'missing-feature-value': 'All six executables reject a bare comment delimiter with located stderr and empty stdout.',
        'old-invalid': 'Missing equals retains byte-identical exit, stdout and stderr within each arm.',
        'changed-lines': 'Exact unified patches match the pinned baseline and only the declared grammar edits.',
        'native-execution': 'All six freshly built ELF programs execute the small fixtures; no throughput measurement.',
    }
    write_json(base / 'result.json', {'kind': 'change-task', 'head': git(repo, 'rev-parse', 'HEAD'),
               'mutation_checks': 0, 'native_artifacts': artifacts,
               'cases': {name: {'passed': True, 'command': command, 'exit_code': 0,
                                'assertion': assertions[name], 'files': bindings} for name in CASES}})
    validate(base, repo, inputs)
    return work


def mutations(base, repo, inputs, work):
    """Separate omitted/modified copies; never change or remove original evidence."""
    reports = []
    records = [json.loads(x) for x in (base / 'commands.jsonl').read_text().splitlines()]
    target = next(r for r in records if r['id'] == 'lang/edited/missing-comment.conf')
    for name in ['changed-input', 'false-success', 'missing-evidence']:
        mutant = work / 'mutants' / name
        def omit(directory, names):
            # Omit one actual stdout log while copying, without deleting any file.
            if name == 'missing-evidence' and Path(directory) == (base / target['stdout_file']).parent:
                return [Path(target['stdout_file']).name]
            return []
        shutil.copytree(base, mutant, ignore=omit)
        if name == 'changed-input':
            with (mutant / 'baseline/lang/harbor.lang').open('a') as f:
                f.write('\n// changed frozen source\n')
        if name == 'false-success':
            changed = [dict(r) for r in records]
            next(r for r in changed if r['id'] == target['id'])['exit_code'] = 0
            (mutant / 'commands.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in changed))
            # Refresh outer hashes too: reject the false semantic claim, not a stale digest.
            r = json.loads((mutant / 'result.json').read_text())
            for case in r['cases'].values():
                case['files']['commands.jsonl'] = sha(mutant / 'commands.jsonl')
            write_json(mutant / 'result.json', r)
        argv = [sys.executable, '-B', str(Path(__file__).resolve()), '--validate', '--repo', str(repo),
                '--inputs', str(inputs), '--evidence', str(mutant)]
        p = subprocess.run(argv, capture_output=True, text=True)
        assert p.returncode != 0, ('accepted mutant', name)
        reports.append({'mutant': name, 'command': shlex.join(argv), 'exit_code': p.returncode,
                        'stdout': p.stdout, 'stderr': p.stderr})
    write_json(base / 'mutation-results.json', reports)
    r = json.loads((base / 'result.json').read_text())
    r['mutation_checks'] = len(reports)
    for case in r['cases'].values():
        case['files']['mutation-results.json'] = sha(base / 'mutation-results.json')
    write_json(base / 'result.json', r)
    validate(base, repo, inputs)


def publish(staged, base):
    """Exchange complete directories atomically on the native Linux replay host.

    A rename of individual files could expose mismatched result/transcript hashes.
    Keep the previous proof at staged, including if the process stops at publication.
    An unavailable exchange operation fails without touching the retained proof.
    """
    rename = ctypes.CDLL(None, use_errno=True).renameat2
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                       ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(staged), -100, os.fsencode(base), 2) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(base))


def transaction(base, repo, inputs, selftest=False):
    # Stage beside the destination so publication is a single filesystem operation.
    # Failures leave both the previous proof and partial diagnostic logs available.
    staged = Path(tempfile.mkdtemp(prefix='.' + base.name + '-pending-', dir=base.parent))
    for name in [*REGISTERED, 'preregistration.json', 'check.py']:
        dest = staged / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base / name, dest)
    for name in ['attempts', 'preregistration-history']:
        if (base / name).exists():
            shutil.copytree(base / name, staged / name)
    work = replay(staged, repo, inputs)
    mutations(staged, repo, inputs, work)
    if selftest:
        failure_checks(staged, repo, inputs)
    validate(staged, repo, inputs)
    publish(staged, base)


def failure_checks(base, repo, inputs):
    """Fail after Lang has emitted records, as a missing Bison tool did originally."""
    def snapshot():
        return {str(p.relative_to(base)): sha(p) for p in base.rglob('*') if p.is_file()}

    before = snapshot()
    run = subprocess.run
    reports = []
    for failure in ['missing-tool', 'timeout', 'interrupt']:
        calls = []

        def fail(argv, **kwargs):
            if argv[:4] == ['nice', '-n', '10', 'bison']:
                calls.append(shlex.join(argv))
                if failure == 'timeout':
                    raise subprocess.TimeoutExpired(argv, kwargs['timeout'])
                if failure == 'interrupt':
                    raise KeyboardInterrupt()
                return subprocess.CompletedProcess(argv, 127, b'', b'bison: unavailable\n')
            return run(argv, **kwargs)

        expected = {'missing-tool': AssertionError, 'timeout': subprocess.TimeoutExpired,
                    'interrupt': KeyboardInterrupt}[failure]
        subprocess.run = fail
        try:
            try:
                transaction(base, repo, inputs)
            except expected:
                pass
            else:
                raise AssertionError('accepted failed replay: ' + failure)
        finally:
            subprocess.run = run
        assert len(calls) == 1 and snapshot() == before, failure
        validate(base, repo, inputs)
        reports.append({'failure': failure, 'injected_at': calls[0],
                        'unchanged_files': len(before), 'validation': 'passed'})
    write_json(base / 'failure-preservation.json', reports)
    result = json.loads((base / 'result.json').read_text())
    for case in result['cases'].values():
        case['files']['failure-preservation.json'] = sha(base / 'failure-preservation.json')
    write_json(base / 'result.json', result)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    for name in ['replay', 'selftest', 'validate']:
        mode.add_argument('--' + name, action='store_true')
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--evidence', type=Path)
    a = p.parse_args()
    repo, inputs = a.repo.resolve(), a.inputs.resolve()
    base = (a.evidence or repo.parent / 'evidence/change-task').resolve()
    assert not base.is_relative_to(repo), 'retain evidence outside product checkout'
    if a.validate:
        validate(base, repo, inputs)
    else:
        transaction(base, repo, inputs, a.selftest)
    print('PASS: six Harbor cases, six native builds, three separately rejected mutants')


if __name__ == '__main__':
    main()
