#!/usr/bin/env python3
"""Exact numeric reference matrix, cross-reader and core round-trip proof.

Artifacts stay in --evidence (outside the source checkout). Each compile and
execution has a durable transcript; failures are assertions, never new skips.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess

ROOT = Path(__file__).resolve().parent.parent
P = argparse.ArgumentParser()
P.add_argument('mode', choices=['arithmetic', 'validation', 'legacy'])
P.add_argument('--compiler', default=os.environ.get('COMPILER', './out/lang_next'))
P.add_argument('--evidence', required=True)
args = P.parse_args()
compiler = str(Path(args.compiler).resolve())
out = Path(args.evidence).resolve()
assert ROOT not in out.parents, 'keep evidence outside the checkout'
out.mkdir(parents=True, exist_ok=True)
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(out / 'cache'))
log = (out / 'execution.txt').open('w')

def run(cmd, *, check=True):
    p = subprocess.run([str(x) for x in cmd], cwd=ROOT, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    log.write(json.dumps([str(x) for x in cmd]) + '\n' + p.stdout + p.stderr + f'\nexit={p.returncode}\n')
    log.flush()
    if check:
        assert p.returncode == 0, f'{cmd}: exit {p.returncode}\n{p.stdout}\n{p.stderr}'
    return p

def compile_source(text, name='input', extra=()):
    source = out / (name + '.lang')
    source.write_text(text)
    ll = out / (name + '.ll')
    run([compiler, source, *extra, '-o', ll])
    return source, ll

def signed(x, bits):
    x %= 1 << bits
    return x - (1 << bits) if x >= (1 << (bits - 1)) else x

def integer_reference(c, av, bv):
    op, src, dst = c['op'], c['src'], c['dst']
    if op in ('trap', 'unreachable'):
        return None
    bits, db = int(src[1:]), int(dst[1:])
    def norm(x):
        return signed(int(x), bits) if src[0] == 'i' else int(x) % (1 << bits)
    a, b = norm(av), norm(bv)
    if op.startswith('convert') or op == 'bitcast':
        if op == 'convert_checked':
            lo = -(1 << (db - 1)) if dst[0] == 'i' else 0
            hi = (1 << (db - (dst[0] == 'i'))) - 1
            if not lo <= a <= hi:
                return None
        r = a
    elif op in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
        return str(int({'eq': a == b, 'ne': a != b, 'lt': a < b,
                        'le': a <= b, 'gt': a > b, 'ge': a >= b}[op]))
    elif op in ('div', 'rem'):
        if b == 0 or (src[0] == 'i' and a == -(1 << (bits - 1)) and b == -1):
            return None
        q = abs(a) // abs(b) * (-1 if (a < 0) != (b < 0) else 1)
        r = q if op == 'div' else a - q * b
    elif op in ('shl', 'shr'):
        if b < 0 or b >= bits:
            return None
        r = a << b if op == 'shl' else a >> b
    elif op in ('and', 'or', 'xor'):
        r = {'and': a & b, 'or': a | b, 'xor': a ^ b}[op]
    else:
        r = {'add': a + b, 'sub': a - b, 'mul': a * b}[op[:3]]
        lo = -(1 << (bits - 1)) if src[0] == 'i' else 0
        hi = (1 << (bits - (src[0] == 'i'))) - 1
        if op.endswith('checked') and not lo <= r <= hi:
            return None
    r = signed(r, db) if dst[0] == 'i' else r % (1 << db)
    return str(signed(r, 64))

def arithmetic():
    cases = json.loads((ROOT / 'test/numeric/cases.json').read_text())
    declarations, schemas = [], []
    for i, c in enumerate(cases):
        op, src, dst = c['op'], c['src'], c['dst']
        arity = 0 if src == 'void' else 1 if op.startswith('convert') or op == 'bitcast' else 2
        values = ['fa', 'fb'] if src.startswith('f') else ['a', 'b']
        operands = ''.join(', ' + x for x in values[:arity])
        expr = f'__core_numeric("{op}", "{dst}", "{src}"{operands})'
        if dst.startswith('f'):
            expr = f'__core_numeric("bitcast", "u{dst[1:]}", "{dst}", {expr})'
        body = f'return {expr};' if dst != 'void' else f'{expr}; return 0;'
        declarations.append(f'func numeric_probe_{i}(a i64, b i64, fa f64, fb f64) i64 {{ {body} }}')
        schemas.append(f'numeric_probe_{i} {op} {dst} {src} {arity}')
    dispatch = [f'extern int64_t numeric_probe_{i}(int64_t,int64_t,double,double);' for i in range(len(cases))]
    dispatch += ['static int64_t (*numeric_probes[])(int64_t,int64_t,double,double) = {',
                 ','.join(f'numeric_probe_{i}' for i in range(len(cases))), '};']
    (out / 'dispatch.h').write_text('\n'.join(dispatch))
    source, ll = compile_source('\n'.join(declarations), 'lang')
    schema, sl = compile_source('include "test/numeric/reader.lang"\n#numeric_fixture{\n' + '\n'.join(schemas) + '\n}\n', 'schema')
    # Re-emit and parse each frontend's closed core. Round-trip executables
    # exercise all boundary vectors too, rather than merely comparing text.
    modules = [('lang', ll), ('schema', sl)]
    for name, input_source in [('lang', source), ('schema', schema)]:
        ast = out / (name + '.ast')
        run([compiler, input_source, '--emit-expanded-ast', '-o', ast])
        parsed = out / (name + '-round.ll')
        run([compiler, ast, '--from-ast', '--ast-source', input_source, '-o', parsed])
        modules.append((name + '-round', parsed))
    oracle = out / 'float-oracle'
    run(['cc', '-O0', '-fno-fast-math', 'test/numeric/float_oracle.c', '-lm', '-o', oracle])
    expected = []
    for c in cases:
        rows = []
        for a, b in c['vectors']:
            if c['src'].startswith('f') or c['dst'].startswith('f'):
                p = run([oracle, c['op'], c['dst'], c['src'], a, b], check=False)
                assert p.returncode in (0, 100), p.stderr
                value = None if p.returncode == 100 else p.stdout.strip()
            else:
                value = integer_reference(c, a, b)
            rows.append(value)
        expected.append(rows)
    checks = 0
    for name, module in modules:
        for opt in ('-O0', '-O2'):
            exe = out / (name + opt)
            run(['clang', opt, module, 'test/numeric/driver.c', '-I', out, '-lm', '-o', exe])
            for i, c in enumerate(cases):
                for (a, b), want in zip(c['vectors'], expected[i]):
                    p = run([exe, i, a, b], check=False)
                    if want is None:
                        assert p.returncode in (-4, -5, -6), (name, opt, c, a, b, p.returncode)
                    else:
                        assert p.returncode == 0 and p.stdout.strip() == want, (name, opt, c, a, b, want, p.stdout, p.stderr)
                    checks += 1
    print(f'PASS {checks} numeric reference executions; {len(cases)} operations/types; lang + schema + both core round-trips; -O0/-O2')

def reject(text, message, *, ast=False, backend='llvm'):
    suffix = '.ast' if ast else '.lang'
    source = out / ('reject-' + str(reject.count) + suffix)
    reject.count += 1
    source.write_text(text)
    target = source.with_suffix('.ll')
    prior = env['LANGBE']; env['LANGBE'] = backend
    p = run([compiler, source, *(['--from-ast'] if ast else []), '-o', target], check=False)
    env['LANGBE'] = prior
    assert p.returncode != 0 and message in p.stderr and str(source) in p.stderr, (source, p.returncode, p.stderr)
    assert not target.exists() or not target.read_bytes(), 'failed compile published an executable module'
reject.count = 0

def validation():
    calls = [
        ('"oops", "i64", "i64", 1, 2', 'unknown or incompatible operation'),
        ('"add_wrap", "u3", "u3", 1, 2', 'unsupported numeric type'),
        ('"add_wrap", "i64", "i64", 1', 'incorrect operand count'),
        ('"add_wrap", "i64", "u64", 1, 2', 'types must match'),
        ('"add_wrap", "f64", "f64", 1.0, 2.0', 'unknown or incompatible operation'),
        ('"add", "f64", "f64", 1, 2', 'operand representation'),
        ('"convert", "i64", "i64", missing', 'operand has no numeric representation'),
        ('"bitcast", "i64", "f32", 1.0', 'equal widths'),
        ('"lt", "u8", "u8", 1, 2', 'comparison result'),
        ('"trap", "i64", "i64"', 'void types'),
        ('123, "i64", "i64", 1, 2', 'literal strings'),
        ('"convert"', 'expected operation'),
    ]
    for call, message in calls:
        reject(f'func main() i64 {{\n return __core_numeric({call});\n}}', message)
    for t in ['wat', 'i0', 'i7', 'u3', 'i128', 'u128', 'i256', 'f16']:
        reject(f'func main() i64 {{ var x {t} = 0; return 0; }}', 'unsupported declared type')
        reject(f'func unknown(x {t}) i64 {{ return 0; }}', 'unsupported declared type')
    reject('func __core_numeric() i64 { return 0; }', 'reserved intrinsic name')
    reject('var x [1]i64 = [__core_numeric("add_wrap", "i64", "i64", 1, 2)]; func main() i64 { return 0; }', 'unsupported global array initializer')
    reject('struct Bad { x i7; } func main() i64 { return 0; }', 'unsupported declared type')
    reject('var x wat = 0; func main() i64 { return 0; }', 'unsupported declared type')
    reject('var x i64 = __core_numeric("add_wrap", "i64", "i64", 1, 2); func main() i64 { return x; }', 'unsupported global initializer')
    reject('(program (func main () nonsense (block (return (number 0)))))', 'invalid-core-type', ast=True)
    reject('(program (func main () (type_base i64) (block (return (binop ! (number 1) (number 2))))))', 'binary-operator', ast=True)
    reject('(program (func main () (type_base i64) (block (return (unop + (number 1))))))', 'unary-operator', ast=True)
    for op in ['mystery', 'ult', 'ugt', 'ule', 'uge']:
        reject(f'(program (func main () (type_base i64) (block (return (binop {op} (number 1) (number 2))))))', 'operator' if op == 'mystery' else 'explicit-numeric-comparison', ast=True)
    reject('(program (func main () (type_bogus i64) (block (return (number 0)))))', 'unknown-core-type', ast=True)
    for backend in ['x86', 'wasm']:
        reject('func main() i64 { return __core_numeric("add_wrap", "i8", "i8", 1, 2); }', 'requires LLVM lowering', backend=backend)
    print(f'PASS {reject.count} numeric/type/operator rejections with source origins')

def legacy():
    for fixture in ['158_cast_literal', '260_float_basic', '261_float_composed', '265_cast_basic', '290_pointer_index_floats']:
        source = ROOT / ('test/suite/' + fixture + '.lang')
        expected = int(source.read_text().splitlines()[0].split(':')[1])
        ll = out / (fixture + '.ll')
        run([compiler, source, '-o', ll])
        for opt in ['-O0', '-O2']:
            exe = out / (fixture + opt)
            run(['clang', opt, ll, '-o', exe])
            p = run([exe], check=False)
            assert p.returncode == expected, (fixture, opt, expected, p.returncode)
    for reader, fixture in [('c','example/c/test_c.lang'), ('forth','example/forth/test_forth.lang'), ('minipy','example/minipy/test_minipy.lang'), ('minilisp','example/minilisp/test_defun.lang')]:
        ll = out / (reader + '.ll')
        run([compiler, fixture, '-o', ll])
        for opt in ['-O0', '-O2']:
            exe = out / (reader + opt)
            run(['clang', opt, ll, '-o', exe]); run([exe])
    print('PASS legacy cast/float/pointer ABI fixtures and C/Forth/Minipy/Minilisp readers at -O0/-O2')

{'arithmetic': arithmetic, 'validation': validation, 'legacy': legacy}[args.mode]()
