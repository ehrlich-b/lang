#!/usr/bin/env python3
"""Trace existing readers through exact numerics and bounded object storage.

All results and generated inputs live in --evidence, outside the checkout.
This checker deliberately uses explicit checks so python -O has identical force.
"""
import argparse
import copy
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test/shared_witness'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(root):
    expected = json.loads((ROOT / 'test/shared_witness/readers.json').read_text())
    for name, sha in expected.items():
        text = (root / name).read_text()
        require(not re.search(r'func\s+(?:layout_|numeric_|llvm_numeric_)', text),
                'reader-local duplicate semantics: ' + name)
        require(digest(root / name) == sha, 'reader contract changed: ' + name)
    for name, tokens in {
        'src/codegen.lang': ['include "src/numeric.lang"', 'include "src/layout.lang"'],
        'src/codegen_llvm.lang': ['layout_query(t, profile, &storage)',
                                 'numeric_validate_tree(func_decl_body(func_node))',
                                 'llvm_numeric_emit(expr)'],
        'src/sexpr_reader.lang': ['span', 'call'],
    }.items():
        text = (root / name).read_text()
        for token in tokens:
            require(token in text, 'missing shared route: ' + token)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiler', type=Path, default=ROOT / 'out/bootstrap_verify/kernel2')
    p.add_argument('--receipt', type=Path, default=ROOT / 'out/verify-receipt.json')
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--controls-only', action='store_true')
    args = p.parse_args()
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64',
            'requires native Linux x86-64 execution')
    base = args.evidence.resolve()
    require(base != ROOT and ROOT not in base.parents, 'evidence must be outside checkout')
    base.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='witness-', dir=base))
    compiler = args.compiler.resolve()
    receipt = args.receipt.resolve()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LANG_CACHE=str(out / 'cache'))
    for key in ('LANG_ROOT', 'LANG_LAYOUT_PROFILE'):
        env.pop(key, None)
    rows = []
    report = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  compiler={'path': str(compiler), 'sha256': digest(compiler)},
                  receipt={'path': str(receipt), 'sha256': digest(receipt)},
                  python_optimized=not __debug__, commands=rows, walkthrough=[],
                  sources={str(p.relative_to(ROOT)): digest(p) for p in
                           [Path(__file__).resolve(), *sorted(FIXTURES.iterdir())] if p.is_file()},
                  target='native Linux x86-64', rejections=[], controls=[])

    # Refuse uncommitted replacements, including a generated AST substituted
    # for the independently reviewed handwritten fixture.
    for name, sha in report['sources'].items():
        committed = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
        require(hashlib.sha256(committed).hexdigest() == sha,
                'witness input differs from committed HEAD: ' + name)

    def run(command, expected=0, diagnostic=None):
        command = [str(x) for x in command]
        if '--emit-expanded-ast' in command:
            require(Path(command[command.index('-o') + 1]).resolve().is_relative_to(out),
                    'generated AST must stay in external evidence')
        input_hashes = {str(Path(x).resolve()): digest(x) for x in command if Path(x).is_file()}
        r = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=240)
        n = len(rows)
        stdout, stderr = out / f'{n}.stdout', out / f'{n}.stderr'
        stdout.write_bytes(r.stdout); stderr.write_bytes(r.stderr)
        rows.append(dict(command=command, cwd=str(ROOT), exit=r.returncode, expected=expected,
                         inputs=input_hashes, stdout=str(stdout), stderr=str(stderr),
                         stdout_sha256=digest(stdout), stderr_sha256=digest(stderr)))
        (out / 'shared-witness.json').write_text(json.dumps(report, indent=2) + '\n')
        require(r.returncode == expected, f'{command}: exit {r.returncode}, expected {expected}: {r.stderr.decode(errors="replace")}')
        if diagnostic:
            require(diagnostic.encode() in r.stderr, 'missing rejection diagnostic: ' + diagnostic)
        return r

    audit(ROOT)
    # The real receipt checker must run before any compiler evidence is trusted.
    run([sys.executable, 'scripts/build_receipt.py', 'check', '--input', receipt, '--compiler', compiler])
    original = json.loads(receipt.read_text())
    require(not original['source']['dirty'], 'witness requires a clean committed build')
    for optimized in (False, True):
        python = [sys.executable] + (['-O'] if optimized else [])
        run(python + ['scripts/build_receipt.py', 'check', '--input', receipt, '--compiler', compiler])
        mutations = [
            ('compiler', lambda x: x['compiler'].update(sha256='0' * 64), 'compiler hash mismatch'),
            ('source', lambda x: x['source']['inputs'].update({'src/layout.lang': '0' * 64}), 'source inputs changed'),
            ('revision', lambda x: x['source'].update(revision='0' * 40), 'stale source revision'),
            ('artifact', lambda x: next(iter(x['artifacts'].values())).update(sha256='0' * 64), 'artifact hash mismatch'),
        ]
        for label, mutate, message in mutations:
            value = copy.deepcopy(original); mutate(value)
            bad = out / f'bad-{label}-{optimized}.json'
            bad.write_text(json.dumps(value))
            run(python + ['scripts/build_receipt.py', 'check', '--input', bad, '--compiler', compiler], 1, message)
        # Actual previous compiler bytes, not only a tampered receipt field.
        run(python + ['scripts/build_receipt.py', 'check', '--input', receipt,
                      '--compiler', ROOT / 'out/bootstrap_verify/ctrusted'], 1, 'compiler hash mismatch')
    # Introduce a reader-local implementation into an external copy. Neither
    # timestamp tricks nor rewriting the source checkout can hide duplication.
    audit_root = out / 'duplicate'
    for name in [*json.loads((ROOT / 'test/shared_witness/readers.json').read_text()), 'src/codegen.lang', 'src/codegen_llvm.lang']:
        target = audit_root / name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    with (audit_root / 'src/sexpr_reader.lang').open('a') as f:
        f.write('\nfunc numeric_reader_duplicate() i64 { return 0; }\n')
    try:
        audit(audit_root)
    except ValueError as error:
        require('duplicate semantics' in str(error), 'wrong reader-local rejection')
        report['duplicate_control'] = str(error)
    else:
        raise ValueError('accepted reader-local semantics')

    source = FIXTURES / 'program.lang'
    handwritten = FIXTURES / 'program.ast'
    vectors = json.loads((FIXTURES / 'expected.json').read_text())['vectors']
    report['expected_vectors'] = vectors

    def execute_leg(label, input_path, extra, expected_vectors):
        module = out / (label + '.ll')
        first_command = len(rows)
        run([compiler, input_path, *extra, '-o', module])
        ir = module.read_text()
        require('add i8' in ir or label == 'operator-control',
                'shared wrap lowering missing')
        require('icmp ult i64' in ir and 'icmp slt i8' in ir,
                'shared comparison lowering missing')
        results = []
        for opt in ('-O0', '-O2'):
            exe = out / (label + opt)
            run(['clang', opt, module, FIXTURES / 'driver.c', '-o', exe])
            for function, a, b, expected in expected_vectors:
                r = run([exe, function, a, b])
                results.append(dict(optimization=opt, function=function, a=a, b=b,
                                    expected=expected, actual=r.stdout.decode().strip()))
        report['walkthrough'].append(dict(reader=label, input=str(input_path),
            input_sha256=digest(input_path), command_range=[first_command, len(rows)],
            services=['numeric_validate_tree', 'llvm_numeric_emit', 'llvm_storage_size', 'layout_query'],
            module=str(module), module_sha256=digest(module), results=results))
        return results

    def check_results(results):
        for result in results:
            require(result['actual'] == result['expected'],
                    'execution mismatch: ' + json.dumps(result, sort_keys=True))

    # This file is a direct handwritten input, never an emitter output.
    check_results(execute_leg('handwritten-core', handwritten, ['--from-ast'], vectors))
    if not args.controls_only:
        check_results(execute_leg('lang', source, [], vectors))
        generated = out / 'generated-roundtrip.ast'
        run([compiler, source, '--emit-expanded-ast', '-o', generated])
        check_results(execute_leg('generated-roundtrip', generated,
                                 ['--from-ast', '--ast-source', source], vectors))

    # Both controls execute real modules at both optimization levels. The same
    # result comparator used above must reject their captured output.
    changed = out / 'operator-control.ast'
    text = handwritten.read_text()
    require(text.count('"add_wrap"') == 1, 'ambiguous arithmetic control')
    changed.write_text(text.replace('"add_wrap"', '"sub_wrap"'))
    wrong_vectors = copy.deepcopy(vectors)
    wrong_vectors[0][3] = '1'  # Independently wrong: (255 + 1) mod 256 is 0.
    wrong_expected = out / 'wrong-expected.json'
    wrong_expected.write_text(json.dumps({'vectors': wrong_vectors}, indent=2) + '\n')
    for label, inp, expected_vectors in [('operator-control', changed, vectors),
                                        ('expected-control', handwritten,
                                         json.loads(wrong_expected.read_text())['vectors'])]:
        results = execute_leg(label, inp, ['--from-ast'], expected_vectors)
        try:
            check_results(results)
        except ValueError as error:
            require('execution mismatch:' in str(error), 'wrong execution control rejection')
            require({r['optimization'] for r in results if r['actual'] != r['expected']} == {'-O0', '-O2'},
                    'control must expose an actual mismatch at both optimization levels')
            report['controls'].append(dict(label=label, rejection=str(error),
                mismatches=[r for r in results if r['actual'] != r['expected']],
                expected_input=str(wrong_expected if label == 'expected-control' else FIXTURES / 'expected.json'),
                expected_sha256=digest(wrong_expected if label == 'expected-control' else FIXTURES / 'expected.json')))
        else:
            raise ValueError('accepted changed arithmetic or expected vector')

    def check_location(stderr, location):
        require(f":{location['line']}:{location['column']}: error:".encode() in stderr,
                'diagnostic location mismatch: ' + json.dumps(location))

    # Byte offsets in diagnostic.read are specified by hand: [4,7) is
    # "bad", line 2 column 3. Parser failures need not retain a node span.
    span_source = FIXTURES / 'diagnostic.read'
    for case in json.loads((FIXTURES / 'rejections.json').read_text()):
        inp = FIXTURES / case['input']
        module = out / (inp.stem + '.ll')
        r = run([compiler, inp, '--from-ast', '--ast-source', span_source,
                 '-o', module], 1, case['diagnostic'])
        require(not module.exists() or module.stat().st_size == 0, 'rejection published output')
        require(str(span_source).encode() in r.stderr, 'missing core input origin')
        if case['located']:
            check_location(r.stderr, case['expected_location'])
        report['rejections'].append(dict(case, input_sha256=digest(inp), exit=r.returncode,
            command_index=len(rows)-1, output_bytes=module.stat().st_size if module.exists() else 0,
            location_verified=case['located']))

    # A valid but shifted span must move the actual numeric diagnostic from
    # column 3 to column 2. Comparing it against column 3 must fail.
    span_control = out / 'shifted-span.ast'
    span_control.write_text((FIXTURES / 'invalid-operation.ast').read_text().replace('span 4 7', 'span 3 7'))
    module = out / 'shifted-span.ll'
    r = run([compiler, span_control, '--from-ast', '--ast-source', span_source,
             '-o', module], 1, 'numeric: unknown or incompatible operation')
    check_location(r.stderr, {'line': 2, 'column': 2})
    try:
        check_location(r.stderr, {'line': 2, 'column': 3})
    except ValueError as error:
        report['controls'].append(dict(label='shifted-span', rejection=str(error),
            expected_column=3, actual_column=2, command_index=len(rows)-1))
    else:
        raise ValueError('accepted shifted source span')
    require(not module.exists() or module.stat().st_size == 0, 'span rejection published output')

    if not args.controls_only:
        # Decimal f32 literals have an existing S-expression parser limitation;
        # keep its literal regression on the Lang reader, explicitly labelled.
        for fixture in ('test/layout/f32_literal.lang', 'test/layout/equivalence.lang'):
            module = out / (Path(fixture).stem + '.ll')
            run([compiler, fixture, '-o', module])
            for opt in ('-O0', '-O2'):
                exe = module.with_name(module.stem + opt)
                run(['clang', opt, module, '-o', exe]); run([exe], 42)
        invalid = [
            ('func main() i64 {\n return __core_numeric("oops", "i64", "i64", 1, 2);\n}', 'unknown or incompatible operation'),
            ('func main() i64 { var a [9223372036854775808]u8; return 0; }', 'fixed-array count exceeds signed size limit'),
            ('func main() i64 { var a [0]void; return 0; }', 'layout: unsupported storage type'),
        ]
        for n, (text, diagnostic) in enumerate(invalid):
            source = out / f'invalid-{n}.lang'; source.write_text(text)
            module = out / f'invalid-{n}-lang.ll'
            r = run([compiler, source, '-o', module], 1, diagnostic)
            require(str(source).encode() in r.stderr, 'missing source origin')
            require(not module.exists() or module.stat().st_size == 0, 'rejection published output')
            report['rejections'].append(dict(input=str(source), input_sha256=digest(source),
                reader='lang', diagnostic=diagnostic, command_index=len(rows)-1,
                phase='lang-parser' if n == 1 else ('numeric-validation' if n == 0 else 'layout')))
        # The independent C oracle rejects aggregates, pointer/function/closure
        # relocations, unknown profiles, overflow and invalid counts explicitly.
        run([sys.executable, 'test/run_storage_layout.py', 'api', '--compiler', compiler,
             '--evidence', out / 'storage-api'])
        for mode in ('arithmetic', 'validation'):
            run([sys.executable, 'test/run_numeric.py', mode, '--compiler', compiler,
                 '--evidence', out / ('numeric-' + mode)])
    for name, sha in report['sources'].items():
        require(digest(ROOT / name) == sha, 'witness input changed during execution: ' + name)
    report['status'] = 'PASS'
    (out / 'shared-witness.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS shared witness:', out / 'shared-witness.json')


if __name__ == '__main__':
    main()
