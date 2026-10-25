#!/usr/bin/env python3
"""Check fixed-array parameter admission without changing the internal call ABI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test/layout_signatures'
ERRORS = {
    'unsupported': 'unsupported storage type (expected scalar or fixed array of scalars)',
    'overflow': 'fixed-array storage exceeds target size limit',
    'count': 'negative fixed-array count',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, default=ROOT / 'out/bootstrap_verify/kernel2')
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    if evidence == ROOT or ROOT in evidence.parents:
        parser.error('evidence must be outside checkout')
    evidence.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='layout-signatures-', dir=evidence))
    compiler = args.compiler.resolve()
    env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LANG_CACHE=str(out / 'cache'))
    for key in ('LANG_ROOT', 'LANG_LAYOUT_PROFILE'):
        env.pop(key, None)
    inputs = [Path(__file__).resolve(), compiler, *sorted(FIXTURES.iterdir())]
    report = dict(python_optimized=not __debug__, compiler=str(compiler),
                  inputs={str(p): digest(p) for p in inputs if p.is_file()},
                  commands=[], failures=[])
    expected = json.loads((FIXTURES / 'expected.json').read_text())

    def run(argv, name, inputs):
        result = subprocess.run(list(map(str, argv)), cwd=ROOT, env=env,
                                capture_output=True, timeout=60)
        stdout, stderr = out / (name + '.stdout'), out / (name + '.stderr')
        stdout.write_bytes(result.stdout)
        stderr.write_bytes(result.stderr)
        report['commands'].append(dict(argv=list(map(str, argv)), cwd=str(ROOT),
            exit_code=result.returncode, inputs={str(p): digest(p) for p in inputs},
            stdout=str(stdout), stdout_sha256=digest(stdout),
            stderr=str(stderr), stderr_sha256=digest(stderr)))
        return result

    for name, expectation in expected.items():
        source = FIXTURES / name
        env['LANGOS'] = expectation.get('target', 'linux')
        module = out / (name + '.ll')
        command = [compiler, source]
        diagnostic_source = source
        used_inputs = [compiler, source]
        if source.suffix == '.ast':
            command += ['--from-ast']
            if expectation.get('location') or expectation.get('ast_source') or expectation.get('error') == 'span':
                diagnostic_source = FIXTURES / 'diagnostic.read'
                command += ['--ast-source', diagnostic_source]
                used_inputs.append(diagnostic_source)
        command += ['-o', module]
        result = run(command, name + '-compile', used_inputs)
        row = report['commands'][-1]
        row.update(module=str(module), module_bytes=module.stat().st_size if module.exists() else None,
                   module_sha256=digest(module) if module.exists() else None)
        errors = []
        text = result.stderr.decode(errors='replace')
        if 'error' in expectation:
            if result.returncode != 1:
                errors.append(f'exit {result.returncode}, expected 1')
            if module.exists() and module.stat().st_size:
                errors.append('rejection left a nonempty module')
            if expectation['error'] == 'span':
                if f'(code {expectation["code"]})' not in text or 'layout:' in text:
                    errors.append('invalid span did not fail before layout')
            else:
                location = expectation['location']
                prefix = f'{diagnostic_source}:{location[0]}:{location[1]}: ' if location else ''
                wanted = prefix + 'error: layout: ' + ERRORS[expectation['error']]
                if text.splitlines() != [wanted]:
                    errors.append(f'expected {wanted!r}, got {text!r}')
        else:
            if result.returncode != 0 or not module.exists() or not module.stat().st_size:
                errors.append(f'valid compilation failed: exit={result.returncode}, stderr={text!r}')
            else:
                ir = module.read_text()
                for fragment in expectation['ir']:
                    if fragment not in ir:
                        errors.append(f'calling convention changed: missing {fragment!r}')
                binary = out / (name + '.bin')
                links = [FIXTURES / expectation['link']] if 'link' in expectation else []
                build = run([os.environ.get('CLANG', 'clang'), '-O0', module, *links, '-o', binary],
                            name + '-assemble', [module, *links])
                if build.returncode != 0:
                    errors.append('valid IR did not assemble/link: ' + build.stderr.decode(errors='replace'))
                else:
                    execute = run([binary], name + '-execute', [binary])
                    if (execute.returncode, execute.stdout, execute.stderr) != (expectation['exit'], b'', b''):
                        errors.append(f'call returned {execute.returncode}, expected {expectation["exit"]}')
        if errors:
            report['failures'].append(dict(input=name, errors=errors))
        print(f'{name}: {"FAIL" if errors else "PASS"}')
    report['status'] = 'FAIL' if report['failures'] else 'PASS'
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Layout signatures: {report["status"]} ({len(expected)} cases); {out}')
    for failure in report['failures']:
        print(json.dumps(failure), file=sys.stderr)
    return 1 if report['failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
