#!/usr/bin/env python3
"""Six small validation cases over retained captures; no compiler or author trial."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

REVISION = '209e4ca1e12a643102e37b58b6e43fe7ce4c5eaf'
SOURCE_HEAD = 'e148de1e1a3bb1a229f3a8369e41e4b0241783e3'
NAMES = ('valid-receipt', 'wrong-head', 'changed-brief', 'missing-stderr',
         'false-success', 'missing-command')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--replay', action='store_true')
    p.add_argument('--selftest', action='store_true')
    a = p.parse_args()
    repo, inputs = a.repo.resolve(), a.inputs.resolve()
    base = Path.cwd().resolve()
    assert not base.is_relative_to(repo), 'evidence must be outside checkout'
    script = repo / 'scripts/comparison_receipt.py'
    module = importlib.util.spec_from_file_location('comparison_receipt', script)
    validator = importlib.util.module_from_spec(module)
    module.loader.exec_module(validator)
    receipt = base / 'receipt.json'
    validator.create(repo, inputs, REVISION, SOURCE_HEAD, receipt)
    original = json.loads(receipt.read_text())
    validator_head = validator.git(repo, 'rev-parse', 'HEAD').decode().strip()
    assert original['source']['head'] == SOURCE_HEAD
    assert original['arms']['lang']['compiler_head'] == SOURCE_HEAD
    assert all('head' not in arm for arm in original['arms'].values())
    # Explicitly distinguish native signal codes from shell 128+N statuses.
    assert validator.termination(-15) == {'kind': 'signal', 'value': 15}
    assert validator.termination(143) == {'kind': 'exit', 'value': 143}
    assert validator.termination(1) == {'kind': 'exit', 'value': 1}
    assert validator.termination(0) == {'kind': 'exit', 'value': 0}
    commands, results = [], {}
    for name in NAMES:
        mutant = copy.deepcopy(original)
        if name == 'wrong-head':
            mutant['source']['head'] = '0' * 40
            for arm in mutant['arms'].values():
                arm['compiler_head'] = '0' * 40
        elif name == 'changed-brief':
            mutant['source']['brief_sha256'] = '0' * 64
            for arm in mutant['arms'].values():
                arm['brief_sha256'] = '0' * 64
        elif name == 'missing-stderr':
            # Missing even when the original stream is empty. Do not delete it.
            mutant['records'][0]['stderr']['path'] = 'absent-stderr.txt'
        elif name == 'false-success':
            row = next(r for r in mutant['records'] if r['arm'] == 'bison'
                       and r['scope'] == 'command' and r['returncode'] == 1)
            row.update(returncode=0, termination={'kind': 'exit', 'value': 0},
                       succeeded=True)
        elif name == 'missing-command':
            del mutant['records'][0]['command']
        fixture = base / 'fixtures' / (name + '.json')
        write(fixture, mutant)
        command = [sys.executable, '-B', str(script), 'check', '--repo', str(repo),
                   '--inputs', str(inputs), '--inputs-revision', REVISION,
                   '--source-head', SOURCE_HEAD,
                   '--receipt', str(fixture), '--evidence', str(base)]
        process = subprocess.run(command, capture_output=True)
        expected = 0 if name == 'valid-receipt' else 1
        assert process.returncode == expected, (name, process.returncode, process.stderr)
        stdout, stderr = base / 'logs' / (name + '.stdout'), base / 'logs' / (name + '.stderr')
        stdout.parent.mkdir(exist_ok=True)
        stdout.write_bytes(process.stdout)
        stderr.write_bytes(process.stderr)
        files = {str(f.relative_to(base)): sha(f) for f in (fixture, stdout, stderr)}
        # Include all raw historical streams as well as the fragment's streams.
        files.update({str(f.relative_to(base)): sha(f) for f in (base / 'streams').iterdir()})
        assertion = ('Accept source-bound captures with exact commands and exit codes' if expected == 0
                     else 'Reject ' + name + ' independently of agreement between arms')
        results[name] = {'passed': True, 'command': command, 'exit_code': process.returncode,
                         'assertion': assertion, 'files': files}
        commands.append({'case': name, 'command': command, 'exit_code': process.returncode,
                         'stdout': str(stdout.relative_to(base)), 'stderr': str(stderr.relative_to(base)),
                         'files': files})
    if a.selftest:
        # Change an actual input in a separate archive copy. Keep the original
        # frozen archive untouched, including its manifest and all ten inputs.
        changed = base / 'changed-inputs'
        changed.mkdir(exist_ok=True)
        for item in json.loads((inputs / 'MANIFEST.json').read_text()):
            target = changed / item['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((inputs / item['path']).read_bytes())
        (changed / 'MANIFEST.json').write_bytes((inputs / 'MANIFEST.json').read_bytes())
        # Read-only object lookup in the existing local archive; no git mutation.
        (changed / '.git').write_text('gitdir: ' + str(inputs / '.git') + '\n')
        (changed / 'trial1/brief.md').write_bytes((inputs / 'trial1/brief.md').read_bytes() + b'\nchanged\n')
        command = [sys.executable, '-B', str(script), 'check', '--repo', str(repo),
                   '--inputs', str(changed), '--inputs-revision', REVISION,
                   '--source-head', SOURCE_HEAD,
                   '--receipt', str(receipt)]
        process = subprocess.run(command, capture_output=True)
        assert process.returncode == 1 and b'changed trial input: trial1/brief.md' in process.stderr
        (base / 'logs/changed-input.stdout').write_bytes(process.stdout)
        (base / 'logs/changed-input.stderr').write_bytes(process.stderr)
        commands.append({'case': 'changed-brief-input-copy', 'command': command,
                         'exit_code': process.returncode,
                         'stdout': 'logs/changed-input.stdout', 'stderr': 'logs/changed-input.stderr',
                         'files': {str(f.relative_to(base)): sha(f) for f in
                                   [changed / 'trial1/brief.md', base / 'logs/changed-input.stdout',
                                    base / 'logs/changed-input.stderr']}})
        # A newer validator commit cannot turn the historical trial into a test
        # of that newer compiler. Exercise both CLI entry points, including
        # regeneration (the old check-only mutant missed this laundering route).
        assert validator_head != SOURCE_HEAD, 'run regression from the validator commit'
        for action in ('create', 'check'):
            target = base / 'rebinding' / 'receipt.json' if action == 'create' else receipt
            target.parent.mkdir(exist_ok=True)
            command = [sys.executable, '-B', str(script), action, '--repo', str(repo),
                       '--inputs', str(inputs), '--inputs-revision', REVISION,
                       '--source-head', validator_head, '--receipt', str(target)]
            process = subprocess.run(command, capture_output=True)
            assert process.returncode == 1 and b'requested source head differs' in process.stderr
            if action == 'create':
                assert not target.exists(), 'rejected creation must not emit a forged receipt'
            stdout = base / 'logs' / ('rebinding-' + action + '.stdout')
            stderr = base / 'logs' / ('rebinding-' + action + '.stderr')
            stdout.write_bytes(process.stdout)
            stderr.write_bytes(process.stderr)
            commands.append({'case': 'rebinding-' + action, 'command': command,
                             'exit_code': process.returncode,
                             'stdout': str(stdout.relative_to(base)),
                             'stderr': str(stderr.relative_to(base)),
                             'files': {str(f.relative_to(base)): sha(f) for f in (stdout, stderr)}})
    (base / 'commands.jsonl').write_text(''.join(json.dumps(c, sort_keys=True) + '\n' for c in commands))
    write(base / 'result.json', {'kind': 'receipt-integrity', 'head': validator_head,
                               'trial_source_head': original['source']['head'],
                               'cases': results, 'mutation_checks': 5,
                               'selftest': a.selftest})
    print('PASS: six receipt cases, five forgeries rejected; signed exits preserved')


if __name__ == '__main__':
    main()
