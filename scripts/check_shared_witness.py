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
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


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
    base = args.evidence.resolve()
    require(base != ROOT and ROOT not in base.parents, 'evidence must be outside checkout')
    base.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='witness-', dir=base))
    compiler = args.compiler.resolve()
    receipt = args.receipt.resolve()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LANG_CACHE=str(out / 'cache'))
    env.pop('LANG_ROOT', None)
    rows = []
    report = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  compiler={'path': str(compiler), 'sha256': digest(compiler)},
                  receipt={'path': str(receipt), 'sha256': digest(receipt)},
                  python_optimized=not __debug__, commands=rows, walkthrough=[])

    def run(command, expected=0, diagnostic=None):
        command = [str(x) for x in command]
        r = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=240)
        n = len(rows)
        stdout, stderr = out / f'{n}.stdout', out / f'{n}.stderr'
        stdout.write_bytes(r.stdout); stderr.write_bytes(r.stderr)
        rows.append(dict(command=command, exit=r.returncode, expected=expected,
                         stdout=str(stdout), stderr=str(stderr)))
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

    if not args.controls_only:
        source = ROOT / 'test/shared_witness/program.lang'
        ast = out / 'program.ast'
        run([compiler, source, '--emit-expanded-ast', '-o', ast])
        core = ast.read_text()
        require('__core_numeric' in core and 'type_array' in core and 'f32' in core,
                'core lost exact operations or fixed arrays')
        vectors = json.loads((ROOT / 'test/shared_witness/expected.json').read_text())['vectors']
        for reader, input_path, extra in [('lang', source, []), ('sexpr', ast, ['--from-ast', '--ast-source', source])]:
            module = out / (reader + '.ll')
            run([compiler, input_path, *extra, '-o', module])
            ir = module.read_text()
            require('add i8' in ir and 'icmp ult i64' in ir and 'icmp slt i8' in ir,
                    'shared exact numeric lowering missing')
            for opt in ('-O0', '-O2'):
                exe = out / (reader + opt)
                run(['clang', opt, module, 'test/shared_witness/driver.c', '-o', exe])
                for function, a, b, expected in vectors:
                    r = run([exe, function, a, b])
                    require(r.stdout.decode().strip() == expected, f'{reader} {opt}: wrong reference result')
            report['walkthrough'].append(dict(reader=reader, syntax=str(input_path), core=str(ast),
                services=['numeric_validate_tree', 'llvm_numeric_emit', 'llvm_storage_size', 'layout_query'],
                module=str(module), expected_vectors='test/shared_witness/expected.json',
                result='20 reference results for this reader at O0/O2; storage result 42'))
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
            for reader in ('lang', 'sexpr'):
                inp, extra = source, []
                if reader == 'sexpr':
                    # Count overflow rejects while parsing the Lang syntax.
                    if n == 1:
                        continue
                    inp = out / f'invalid-{n}.ast'
                    run([compiler, source, '--emit-expanded-ast', '-o', inp])
                    extra = ['--from-ast', '--ast-source', source]
                module = out / f'invalid-{n}-{reader}.ll'
                r = run([compiler, inp, *extra, '-o', module], 1, diagnostic)
                require(str(source).encode() in r.stderr, 'missing source origin')
                require(not module.exists() or module.stat().st_size == 0, 'rejection published output')
        # Independent byte offsets: line 2, column 3 is byte 4 in this source.
        span_source = out / 'span.read'; span_source.write_text('x\n  bad\n')
        for label, start, end, diagnostic in [('valid', '4', '7', ':2:3: error: numeric:'),
                ('negative', '-1', '7', 'invalid-span-number'),
                ('outside', '4', '99', 'invalid-span')]:
            span_ast = out / (label + '.ast')
            span_ast.write_text('(program (func main () (type_base i64) (block (return '
                f'(span {start} {end} (call (ident __core_numeric) (string "oops") (string "i64") (string "i64") (number 1) (number 2)))'
                '))))\n')
            run([compiler, span_ast, '--from-ast', '--ast-source', span_source,
                 '-o', out / (label + '.ll')], 1, diagnostic)
        # The independent C oracle rejects aggregates, pointer/function/closure
        # relocations, unknown profiles, overflow and invalid counts explicitly.
        run([sys.executable, 'test/run_storage_layout.py', 'api', '--compiler', compiler,
             '--evidence', out / 'storage-api'])
        for mode in ('arithmetic', 'validation'):
            run([sys.executable, 'test/run_numeric.py', mode, '--compiler', compiler,
                 '--evidence', out / ('numeric-' + mode)])
    report['status'] = 'PASS'
    (out / 'shared-witness.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS shared witness:', out / 'shared-witness.json')


if __name__ == '__main__':
    main()
