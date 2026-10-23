#!/usr/bin/env python3
"""Independent integer oracle for the explicit N1 core AST contract."""
import argparse
import ctypes
import json
import operator
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MODEL = json.loads((ROOT / 'test/numeric/model.json').read_text())
MASK = (1 << 64) - 1


def integer(bits, signed, value):
    residue = value % (2 ** bits)
    return residue - 2 ** bits if signed and residue >= 2 ** (bits - 1) else residue


def carrier(value):
    return integer(64, True, value)


def matrix():
    """Python integers model mathematical values; no LLVM/Wasm predicates."""
    operations, samples = [], []
    rng = random.Random(MODEL['seed'])
    types = [(sign + str(bits), bits, sign == 'i')
             for bits in MODEL['widths'] for sign in MODEL['signs']]
    predicates = dict(eq=operator.eq, ne=operator.ne, lt=operator.lt,
                      le=operator.le, gt=operator.gt, ge=operator.ge)
    for name, bits, signed in types:
        boundaries = [0, 1, 2 ** (bits - 1) - 1, 2 ** (bits - 1),
                      2 ** (bits - 1) + 1, 2 ** bits - 1, 2 ** bits,
                      2 ** bits + 1, -1, -2, -(2 ** (bits - 1)) - 1]
        values = boundaries + [rng.getrandbits(64) for _ in range(MODEL['random_samples'])]
        for op in MODEL['comparisons']:
            index = len(operations)
            operations.append(f'(int_compare {op} (type_base {name}) (ident a) (ident b))')
            pairs = [(a, b) for a in boundaries for b in boundaries]
            pairs += list(zip(values, reversed(values)))
            for a, b in pairs:
                want = int(predicates[op](integer(bits, signed, a), integer(bits, signed, b)))
                samples.append([index, str(carrier(a)), str(carrier(b)), str(want)])
        for dest, dst_bits, dst_signed in types:
            op = 'extend' if dst_bits > bits else 'truncate' if dst_bits < bits else 'reinterpret'
            index = len(operations)
            operations.append(f'(int_convert {op} (type_base {name}) (type_base {dest}) (ident a))')
            for a in values:
                mathematical = integer(bits, signed, a)
                want = carrier(integer(dst_bits, dst_signed, mathematical))
                samples.append([index, str(carrier(a)), '0', str(want)])
    # Composition, parameter evaluation, and nested conversions/comparisons.
    index = len(operations)
    operations.append('(int_compare lt (type_base i16) '
                      '(int_convert extend (type_base i8) (type_base i16) (ident a)) (ident b))')
    for a in range(256):
        samples.append([index, str(a), '0', str(int(integer(8, True, a) < 0))])
    for expr, want in [
        ('(int_compare gt (type_base u64) (number 18446744073709551615) (number 9223372036854775807))', 1),
        ('(int_compare lt (type_base i8) (number -128) (number 0))', 1),
        ('(int_convert extend (type_base i8) (type_base i64) (number -128))', -128),
        ('(int_convert truncate (type_base u64) (type_base u32) (number 18446744073709551615))', 4294967295),
    ]:
        samples.append([len(operations), '0', '0', str(want)])
        operations.append(expr)
    return operations, samples


def program(operations):
    statements = '\n'.join(
        f'(if (binop == (ident sample) (number {i})) (block (return {expression})))'
        for i, expression in enumerate(operations))
    return ('(program (func main ((param sample (type_base i64)) '
            '(param a (type_base i64)) (param b (type_base i64))) (type_base i64) '
            f'(block {statements} (return (number 0)))))\n')


class Runner:
    def __init__(self, compiler, output):
        self.compiler = str(Path(compiler).resolve())
        output.mkdir(parents=True, exist_ok=True)
        self.output = Path(tempfile.mkdtemp(prefix='numeric-', dir=output)).resolve()
        self.counter = 0

    def run(self, command, *, env=None, success=True):
        self.counter += 1
        result = subprocess.run(command, env=env, capture_output=True, timeout=180)
        prefix = self.output / f'command-{self.counter:03}'
        prefix.with_suffix('.json').write_text(json.dumps({'command': command, 'exit': result.returncode}) + '\n')
        prefix.with_suffix('.stdout').write_bytes(result.stdout)
        prefix.with_suffix('.stderr').write_bytes(result.stderr)
        if success and result.returncode:
            raise AssertionError(f'{command}: exit {result.returncode}: {result.stderr.decode(errors="replace")}')
        return result

    def compile(self, source, backend, label, *, success=True):
        output = self.output / (label + ('.ll' if backend == 'llvm' else '.wasm'))
        env = dict(os.environ, LANGBE=backend, LANGOS='linux' if backend == 'llvm' else 'wasm',
                   LANG_CACHE=str(self.output / 'cache'))
        result = self.run([self.compiler, str(source), '--from-ast', '--ast-source',
                           'test/numeric/origin.txt', '-o', str(output)], env=env, success=success)
        return output, result

    def check(self, source, samples, label):
        sample_file = self.output / (label + '-samples.json')
        sample_file.write_text(json.dumps(samples) + '\n')
        for backend in ('llvm', 'wasm'):
            output, _ = self.compile(source, backend, label + '-' + backend)
            if backend == 'llvm':
                for optimization in ('-O0', '-O2'):
                    library = self.output / (label + optimization + '.so')
                    self.run(['clang', optimization, '-shared', '-fPIC', str(output), '-o', str(library)])
                    probe = ctypes.CDLL(str(library)).main
                    probe.argtypes = [ctypes.c_int64] * 3
                    probe.restype = ctypes.c_int64
                    actual = [str(probe(int(i), int(a), int(b))) for i, a, b, _ in samples]
                    (self.output / (label + optimization + '-actual.json')).write_text(json.dumps(actual) + '\n')
                    for sample, got in zip(samples, actual):
                        assert got == sample[3], f'oracle mismatch {backend}/{optimization}: {sample}, got {got}'
            else:
                self.run(['node', 'test/numeric/oracle.js', str(output), str(sample_file)])
        print(f'PASS {label}: {len(samples)} independent full-width results on native O0/O2 and direct Wasm', flush=True)

    def oracle(self):
        operations, samples = matrix()
        source = self.output / 'matrix.ast'
        source.write_text(program(operations))
        self.check(source, samples, 'matrix')
        for i, expression in enumerate(MODEL['rejections']):
            source = self.output / f'reject-{i}.ast'
            source.write_text(program([f'(span 15 31 {expression})']))
            for backend in ('llvm', 'wasm'):
                output, result = self.compile(source, backend, f'reject-{i}-{backend}', success=False)
                assert result.returncode != 0, f'accepted unsupported operation: {expression}'
                assert not output.exists(), 'partial output after rejected integer operation'
                assert b'test/numeric/origin.txt:2:1: error:' in result.stderr, result.stderr
        print(f'PASS rejection: {len(MODEL["rejections"])} unsupported operations/types on both backends')

    def roundtrip(self):
        import re
        tokens = lambda text: re.findall(r'\(|\)|[^\s()]+', text)
        operations, samples = matrix()
        matrix_source = self.output / 'roundtrip-matrix.ast'
        matrix_source.write_text(program(operations))
        matrix_emitted = self.output / 'roundtrip-matrix-emitted.ast'
        self.run([self.compiler, str(matrix_source), '--from-ast', '--emit-ast',
                  '-o', str(matrix_emitted)])
        assert tokens(matrix_source.read_text()) == tokens(matrix_emitted.read_text())
        self.check(matrix_emitted, samples, 'all-types-roundtrip')
        source = ROOT / 'test/numeric/roundtrip.ast'
        original = source.read_text()
        emitted = self.output / 'emitted.ast'
        reemitted = self.output / 'reemitted.ast'
        env = dict(os.environ, LANGBE='llvm', LANGOS='linux')
        for src, dst in [(source, emitted), (emitted, reemitted)]:
            self.run([self.compiler, str(src), '--from-ast', '--ast-source',
                      'test/numeric/origin.txt', '--emit-ast', '-o', str(dst)], env=env)
        assert emitted.read_bytes() == reemitted.read_bytes(), 'AST did not reach a fixed point'
        # Whitespace-independent exact token identity retains operations, both
        # conversion types, signedness, widths, and byte spans.
        import re
        tokens = lambda text: re.findall(r'\(|\)|[^\s()]+', text)
        assert tokens(original) == tokens(emitted.read_text()), emitted.read_text()
        samples = [[0, str(-(1 << 63)), '1', '0'], [0, '1', str(-(1 << 63)), '1'],
                   [1, '255', '0', '-1'], [1, '128', '0', '-128']]
        self.check(source, samples, 'original')
        self.check(emitted, samples, 'roundtrip')
        # Mutate only the operation after re-emission; diagnostics must retain
        # the exact original range and source coordinates on both backends.
        invalid = self.output / 'origin-error.ast'
        invalid.write_text(emitted.read_text().replace('int_compare lt', 'int_compare add'))
        for backend in ('llvm', 'wasm'):
            _, result = self.compile(invalid, backend, 'origin-error-' + backend, success=False)
            assert result.returncode and b'test/numeric/origin.txt:2:1: error:' in result.stderr, result.stderr
        print('PASS roundtrip: exact tokens, stable AST, executable semantics and origin diagnostics')
        for backend in ('llvm', 'wasm'):
            target = self.output / ('roundtrip-runtime.ll' if backend == 'llvm' else 'roundtrip-runtime.wasm')
            env = dict(os.environ, LANGBE=backend, LANGOS='linux' if backend == 'llvm' else 'wasm')
            self.run([self.compiler, 'test/numeric/roundtrip_runtime.lang', '-o', str(target)], env=env)
            if backend == 'llvm':
                binary = self.output / 'roundtrip-runtime'
                self.run(['clang', '-O2', str(target), '-o', str(binary)])
                self.run([str(binary)])
            else:
                self.run(['node', 'test/wasm_host.js', str(target)])
        print('PASS runtime roundtrip: parse/emit and origin inspection inside native and direct Wasm; all 112 type/operation combinations')


def numeric_reference():
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
            storage = c.get('storage', 'direct')
            prefix = ''
            if storage != 'direct':
                prefix = f'var carrier {storage} = {expr}; '
                expr = 'carrier'
            if dst.startswith('f'):
                expr = f'__core_numeric("bitcast", "u{dst[1:]}", "{dst}", {expr})'
            body = prefix + (f'return {expr};' if dst != 'void' else f'{expr}; return 0;')
            declarations.append(f'func numeric_probe_{i}(a i64, b i64, fa f64, fb f64) i64 {{ {body} }}')
            schemas.append(f'numeric_probe_{i} {op} {dst} {src} {arity} {storage}')
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
        for call, message in calls[:6]:
            if message != 'operand representation':
                reject(f'func main() i64 {{ return 0; __core_numeric({call}); }}', message)
        reject('func main() i64 { return 0; var dead i7 = 0; }', 'unsupported declared type')
        reject('func main() i64 { var x f32 = 1.0; return 0; }', 'f32 initializer requires an explicit numeric conversion')
        reject('func add(a f32, b f32) f64 { return a + b; }', 'legacy f32 binary operands require explicit numeric operations')
        for t in ['wat', 'i0', 'i7', 'u3', 'i128', 'u128', 'i256', 'f16']:
            reject(f'func main() i64 {{ var x {t} = 0; return 0; }}', 'unsupported declared type')
            reject(f'func unknown(x {t}) i64 {{ return 0; }}', 'unsupported declared type')
            for backend in ['llvm', 'x86']:
                reject(f'effect Ask(i64, {t}) i64\nfunc main() i64 {{ return 0; }}',
                       'unsupported declared type', backend=backend)
                reject(f'effect Ask(i64) {t}\nfunc main() i64 {{ return 0; }}',
                       'unsupported declared type', backend=backend)
        for backend in ['llvm', 'x86']:
            reject('effect Ask(i7) wat\nfunc main() i64 { return handle { perform Ask(300) } with { return(v) => v, Ask(x, k) => { resume k(x + 1); } }; }',
                   'unsupported declared type', backend=backend)
            for params, result in [('(type_base i7)', '(type_base i64)'),
                                   ('(type_base i64)', '(type_base wat)'),
                                   ('(type_ptr (type_base u128))', '(type_base i64)')]:
                reject(f'(program (effect Ask ({params}) {result}) (func main () (type_base i64) (block (return (number 0)))))',
                       'unsupported declared type', ast=True, backend=backend)
        reject('effect Fail(i64) i64\nfunc main() i64 { return handle { perform Fail(1); } with { Fail(e) => __core_numeric("oops", "i64", "i64", 1, 2) }; }', 'unknown or incompatible operation')
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['oracle', 'roundtrip'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compiler', default=os.environ.get('COMPILER', 'out/lang_next'))
    args = parser.parse_args()
    os.chdir(ROOT)
    runner = Runner(args.compiler, args.output.resolve())
    print(f'Evidence: {runner.output}', flush=True)
    getattr(runner, args.mode)()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ('arithmetic', 'validation', 'legacy'):
        numeric_reference()
    else:
        main()
