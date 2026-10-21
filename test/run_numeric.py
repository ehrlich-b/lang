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
    main()
