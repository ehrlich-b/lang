#!/usr/bin/env python3
"""Exercise real witness provenance from the repository and a shadow caller cwd."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_report(path, compiler, receipt):
    report = json.loads(path.read_text())
    require(report.get('status') == 'PASS', 'incomplete real witness')
    # Independent list: do not derive expected identities from recorded inputs
    # or the checker's path resolver. All these paths are fixed contract inputs.
    expected = {
        'scripts/build_receipt.py': [ROOT / 'scripts/build_receipt.py', receipt, compiler],
        'test/layout/f32_literal.lang': [compiler, ROOT / 'test/layout/f32_literal.lang'],
        'test/layout/equivalence.lang': [compiler, ROOT / 'test/layout/equivalence.lang'],
        'test/run_storage_layout.py': [ROOT / 'test/run_storage_layout.py', compiler],
        'test/run_numeric.py': [ROOT / 'test/run_numeric.py', compiler],
        str(ROOT / 'test/shared_witness/program.ast'): [compiler, ROOT / 'test/shared_witness/program.ast'],
        str(ROOT / 'test/shared_witness/program.lang'): [compiler, ROOT / 'test/shared_witness/program.lang'],
    }
    identities = {}
    for token, paths in expected.items():
        # The first receipt row uses the genuine receipt, before negative controls.
        row = next((r for r in report['commands'] if token in r['command']), None)
        require(row is not None, 'missing expected command: ' + token)
        executable = Path(sys.executable).resolve() if token.endswith('.py') else compiler
        wanted = {str(p.resolve()): digest(p) for p in [executable, *paths]}
        require(row['inputs'] == wanted, 'input provenance mismatch: ' + token)
        identities[token] = wanted
    for row in report['commands']:
        require(row['cwd'] == str(ROOT), 'wrong execution cwd')
        require(row['exit'] == row['expected'], 'unchecked command failure')
        for flag in ('-o', '--evidence'):
            if flag in row['command']:
                output = Path(row['command'][row['command'].index(flag) + 1])
                require(str(output.resolve()) not in row['inputs'], 'output recorded as input')
    require(report.get('duplicate_control'), 'missing duplicate-semantics refusal')
    require({r['label'] for r in report['controls']} ==
            {'operator-control', 'expected-control', 'shifted-span'}, 'missing semantic refusals')
    return identities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    args = parser.parse_args()
    base = args.evidence.resolve()
    require(base != ROOT and ROOT not in base.parents, 'evidence must be outside checkout')
    base.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='provenance-', dir=base))
    caller = out / 'caller with spaces'
    caller.mkdir()
    for name in ('scripts/build_receipt.py', 'test/layout/f32_literal.lang',
                 'test/layout/equivalence.lang', 'test/run_storage_layout.py', 'test/run_numeric.py'):
        shadow = caller / name
        shadow.parent.mkdir(parents=True, exist_ok=True)
        shadow.write_bytes(b'caller shadow: must never be read or hashed\n')
        require(digest(shadow) != digest(ROOT / name), 'ineffective shadow control')
    compiler = out / 'compiler with spaces'
    shutil.copy2(args.compiler.resolve(), compiler)
    receipt = args.receipt.resolve()
    python = [sys.executable] + (['-O'] if not __debug__ else [])
    rows = []
    report = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  python_optimized=not __debug__, commands=rows,
                  inputs={str(p): digest(p) for p in [Path(__file__).resolve(),
                      ROOT / 'scripts/check_shared_witness.py', args.compiler.resolve(), receipt]},
                  shadows={str(p): digest(p) for p in caller.rglob('*') if p.is_file()})

    def run(label, argv, cwd, expected=0):
        result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=900,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        stdout, stderr = out / (label + '.stdout'), out / (label + '.stderr')
        stdout.write_bytes(result.stdout); stderr.write_bytes(result.stderr)
        rows.append(dict(argv=list(map(str, argv)), cwd=str(cwd), exit_code=result.returncode,
                         expected_exit=expected, stdout=str(stdout), stderr=str(stderr),
                         stdout_sha256=digest(stdout), stderr_sha256=digest(stderr)))
        (out / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
        require(result.returncode == expected, label + ': unexpected exit; see ' + str(stderr))
        return result

    reports = []
    for label, cwd in [('repository', ROOT), ('external', caller)]:
        result = run(label, [*python, str(ROOT / 'scripts/check_shared_witness.py'),
                     '--compiler', str(compiler), '--receipt', str(receipt),
                     '--evidence', str(out / label)], cwd)
        path = Path(result.stdout.decode().strip().split('PASS shared witness: ')[-1])
        reports.append(verify_report(path, compiler, receipt))
    require(reports[0] == reports[1], 'cwd changed input identities or bytes')
    report['expected_inputs'] = reports[0]

    # Probe the production resolver with real files, including a preexisting
    # output and flag-shaped file. No caller cwd change is needed in production.
    spec = importlib.util.spec_from_file_location('witness', ROOT / 'scripts/check_shared_witness.py')
    witness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(witness)
    fixture = out / 'execution cwd with spaces'
    fixture.mkdir()
    relative = fixture / 'input with spaces'
    absolute = out / 'absolute input with spaces'
    output = fixture / 'existing output'
    flag = fixture / '--flag'
    scalar = fixture / '42'
    for p in (relative, absolute, output, flag, scalar):
        p.write_text('execution input: ' + p.name)
    command = [sys.executable, str(relative.relative_to(fixture)), str(absolute), '--flag', '42', '-o', output.name]
    wanted = {str(p.resolve()): digest(p) for p in (Path(sys.executable), relative, absolute)}
    before = Path.cwd()
    try:
        os.chdir(caller)
        actual = witness.command_inputs(command, fixture, [command[1], command[2]])
    finally:
        os.chdir(before)
    require(actual == wanted, 'spaces, absolute input or existing-output classification failed')
    report['resolver_probe'] = dict(argv=command, cwd=str(fixture), inputs=actual,
                                    excluded=[str(flag), str(scalar), str(output)])

    # Run a disposable copy of the actual checker with only old input resolution
    # restored. Keep ROOT explicit so every semantic/committed-fixture check runs.
    checker = (ROOT / 'scripts/check_shared_witness.py').read_text()
    needle = 'input_hashes = command_inputs(command, ROOT, inputs)'
    require(checker.count(needle) == 1, 'ambiguous old-resolution mutation')
    mutation = checker.replace('ROOT = Path(__file__).resolve().parent.parent', 'ROOT = Path(' + repr(str(ROOT)) + ')')
    mutation = mutation.replace(needle,
        'input_hashes = {str(Path(x).resolve()): digest(x) for x in command if Path(x).is_file()}')
    # Copying the checker changes __file__; bind its committed-source audit to
    # the genuine checker while leaving the mutated run implementation active.
    mutation = mutation.replace('Path(__file__).resolve(), *sorted(FIXTURES.iterdir())',
                                "ROOT / 'scripts/check_shared_witness.py', *sorted(FIXTURES.iterdir())")
    old = out / 'old-resolution.py'
    old.write_text(mutation)
    result = run('old-resolution', [*python, str(old), '--compiler', str(compiler),
                 '--receipt', str(receipt), '--evidence', str(out / 'old-resolution')], caller)
    mutated_report = Path(result.stdout.decode().strip().split('PASS shared witness: ')[-1])
    try:
        verify_report(mutated_report, compiler, receipt)
    except ValueError as error:
        require('input provenance mismatch:' in str(error), 'wrong mutation refusal')
        report['old_resolution_refusal'] = str(error)
    else:
        raise ValueError('old-resolution mutation escaped regression')

    # Dirty handwritten fixtures must still refuse before trusting a compiler.
    # Use an external clone; never change the candidate checkout to run a control.
    dirty = out / 'dirty-checkout'
    run('dirty-clone', ['git', 'clone', '--no-hardlinks', '--quiet', str(ROOT), str(dirty)], caller)
    with (dirty / 'test/shared_witness/program.ast').open('a') as f:
        f.write('\n; dirty fixture control\n')
    result = run('dirty-fixture', [*python, str(dirty / 'scripts/check_shared_witness.py'),
                 '--compiler', str(compiler), '--receipt', str(receipt),
                 '--evidence', str(out / 'dirty-evidence')], caller, 1)
    require(b'witness input differs from committed HEAD: test/shared_witness/program.ast' in result.stderr,
            'wrong dirty fixture refusal')
    report['status'] = 'PASS'
    (out / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS witness provenance:', out / 'provenance.json')


if __name__ == '__main__':
    main()
