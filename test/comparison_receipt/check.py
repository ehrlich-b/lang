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
    validator.create(repo, inputs, REVISION, receipt)
    original = json.loads(receipt.read_text())
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
                arm['head'] = '0' * 40
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
    (base / 'commands.jsonl').write_text(''.join(json.dumps(c, sort_keys=True) + '\n' for c in commands))
    write(base / 'result.json', {'kind': 'receipt-integrity', 'head': original['source']['head'],
                               'cases': results, 'mutation_checks': 5,
                               'selftest': a.selftest})
    print('PASS: six receipt cases, five forgeries rejected; signed exits preserved')


if __name__ == '__main__':
    main()
