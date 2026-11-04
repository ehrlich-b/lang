#!/usr/bin/env python3
"""Small, retained regression fragments for compiler table and output growth."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'benchmark/compile'))
from gen import generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=['generated', 'tables', 'budgets', 'targets'], required=True)
    parser.add_argument('--output', type=Path, required=True, help='artifact directory outside the checkout')
    parser.add_argument('--logs', type=Path, required=True)
    args = parser.parse_args()
    os.chdir(ROOT)
    output = args.output.resolve()
    logs = args.logs.resolve()
    if ROOT in output.parents or ROOT in logs.parents:
        parser.error('evidence must be outside the checkout')
    output.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    compiler = Path(os.environ.get('COMPILER', 'out/lang_next')).resolve()
    env = dict(os.environ, LANGBE='llvm', LANGOS='macos' if sys.platform == 'darwin' else 'linux',
               LANG_CACHE=str(output / 'cache'))
    rows = []

    def check(name, command, *, success=True, diagnostic=None, run_env=None, code=None):
        result = subprocess.run(list(map(str, command)), env=run_env or env, capture_output=True, timeout=180)
        (logs / (name + '.stdout')).write_bytes(result.stdout)
        (logs / (name + '.stderr')).write_bytes(result.stderr)
        good = result.returncode == 0 if success else result.returncode == 1
        if code is not None:
            good = result.returncode == code
        if diagnostic:
            good &= diagnostic.encode() in result.stderr
        row = {'name': name, 'command': list(map(str, command)), 'exit': result.returncode, 'pass': bool(good)}
        rows.append(row)
        print(('PASS ' if good else 'FAIL ') + name, flush=True)
        if not good:
            print(result.stderr.decode(errors='replace')[-3000:], flush=True)
            raise RuntimeError(name)
        return result

    def source(name, text):
        path = output / (name + '.lang')
        path.write_text(text)
        return path

    def native(name, path, execute=True):
        ir = output / (name + '.ll')
        check(name + '-emit', [compiler, path, '-o', ir])
        if execute:
            binary = output / name
            check(name + '-link', ['clang', '-O0', ir, '-o', binary])
            check(name + '-run', [binary])
        return ir

    try:
        if args.group == 'generated':
            path = output / 'program-10000.lang'
            with path.open('w') as stream:
                generate(10000, stream)
            assert len(path.read_text().splitlines()) == 10000
            native('program-10000', path)
            # Generator shape and exact counts at all required sizes, without a full-size emit.
            import io
            for size in (10000, 100000, 1000000):
                stream = io.StringIO()
                generate(size, stream)
                text = stream.getvalue()
                assert len(text.splitlines()) == size
                assert 'struct S0 {' in text and 'func work32(' in text and 'work0(p.a + p.b)' in text
            print('PASS generator shape at 10k/100k/1M; full-size emission/timing DEFERRED')
            # Count only tiny samples: each later group adds the same tokens,
            # while the last sample measures the 1M input's 28 padding lines.
            counts = {}
            for size in (36, 68, 96):
                import io
                stream = io.StringIO()
                generate(size, stream)
                sample = source(f'token-shape-{size}', stream.getvalue())
                result = check(f'token-shape-{size}', [compiler, sample, '--dump-tokens'])
                counts[size] = len(result.stdout.splitlines())
            groups = (1000000 - 4) // 32
            required = counts[36] + (groups - 1) * (counts[68] - counts[36]) + counts[96] - counts[68]
            assert counts[68] - counts[36] == 179, counts
            assert 1048576 < required < 16777216, required
            print(f'PASS inferred 1M token count {required} fits explicit benchmark node budget')

        if args.group == 'tables':
            # One small input crosses the old 4000 declarations, 3000 functions,
            # 200 structs, 2000 globals and 3000 LLVM-string allocations.
            text = ''.join(f'struct T{i} {{ a i64; }}\n' for i in range(201))
            text += ''.join(f'var g{i} i64 = {i};\n' for i in range(2001))
            text += ''.join(f'func item{i}() i64 {{ var s *u8 = "text{i}"; return {i}; }}\n' for i in range(3001))
            text += 'func main() i64 { var t T200; t.a = item3000(); if t.a + g2000 != 5000 { return 1; } return 0; }\n'
            path = source('old-table-boundaries', text)
            native('old-table-boundaries', path)
            ast = output / 'tables.ast'
            check('tables-save-ast', [compiler, path, '--emit-ast', '-o', ast])
            ir = output / 'tables-from-ast.ll'
            check('tables-from-ast', [compiler, '--from-ast', ast, '-o', ir])
            binary = output / 'tables-from-ast'
            check('tables-ast-link', ['clang', '-O0', ir, '-o', binary])
            check('tables-ast-run', [binary])
            # A UTF-8 literal expands into escaped bytes: a 3 MB source crosses
            # 8 MiB of output while staying below the default host byte budget.
            long_string = source('old-output-boundary', 'func main() i64 { var s *u8 = "' + 'é' * 1500000 + '"; return 0; }\n')
            ir = native('old-output-boundary', long_string, execute=False)
            assert ir.stat().st_size > 8388608, ir.stat().st_size
            print(f'PASS output grew beyond 8 MiB ({ir.stat().st_size} bytes)')
            for fixture, diagnostic in [('288_parameter_limit', 'parameter limit exceeded (maximum 16)'),
                                        ('289_call_argument_limit', 'call argument limit exceeded (maximum 16)')]:
                check(fixture, [compiler, 'run', f'test/suite/{fixture}.lang'], success=False, diagnostic=diagnostic)
                stderr = (logs / (fixture + '.stderr')).read_text()
                assert f'test/suite/{fixture}.lang:2:' in stderr
            native('parameter-boundary', ROOT / 'test/suite/290_parameter_boundary.lang')
            native('string-key-bytes', ROOT / 'test/suite/291_string_key_bytes.lang')
            # Existing name/arity semantics, macro reader expansion and later struct use.
            reader_ir = output / 'reader-regression.ll'
            check('reader-regression-emit', [compiler, 'example/tiny/test_tiny.lang', '-o', reader_ir])
            reader_bin = output / 'reader-regression'
            check('reader-regression-link', ['clang', '-O0', reader_ir, '-o', reader_bin])
            check('reader-regression-run', [reader_bin], code=42)

        if args.group == 'budgets':
            path = source('host-budget', 'func main() i64 { return 0; }\n')
            check('host-byte-budget', [compiler, path, '-o', output / 'budget.ll'], success=False,
                  diagnostic='byte-limit', run_env=dict(env, LANG_HOST_MAX_BYTES='16'))
            probe = ROOT / 'test/profile_limits_probe.lang'
            native('profile-probe', probe, execute=False)
            binary = output / 'profile-probe'
            check('profile-probe-link', ['clang', '-O0', output / 'profile-probe.ll', '-o', binary])
            # Tiny exact-boundary and over-limit cases exercise every consumer
            # of the same host node setting, without emitting the deferred sizes.
            for mode, diagnostic in [('source-nodes', 'source-nodes'), ('origin-nodes', 'origin-budget'),
                                     ('validate-nodes', 'ast-nodes'), ('emit-nodes', 'ast-nodes')]:
                check(mode + '-boundary', [binary, mode], run_env=dict(env, LANG_HOST_MAX_NODES='3'))
                check(mode + '-over', [binary, mode], success=False, diagnostic=diagnostic,
                      run_env=dict(env, LANG_HOST_MAX_NODES='2'))
            for setting, expected in [('', 1048576), ('1', 1), ('16777216', 16777216)]:
                result = check('node-setting-' + (setting or 'default'), [binary, 'node-setting'],
                               run_env=dict(env, LANG_HOST_MAX_NODES=setting))
                assert result.stdout.strip() == str(expected).encode(), result.stdout
            for i, setting in enumerate(['0', '-1', 'x', '16777217', '999999999999999999999999999999']):
                check(f'node-setting-invalid-{i}', [binary, 'node-setting'], success=False,
                      diagnostic='invalid-node-limit', run_env=dict(env, LANG_HOST_MAX_NODES=setting))
            check('llvm-output-budget', [binary, 'llvm-output'], success=False, diagnostic='LLVM output buffer overflow')
            # Memory and multiplication guards call the production storage functions.
            prefix = '''include "std/core.lang"\ninclude "src/compiler_tables.lang"\n'''
            for name, body, diagnostic in [
                ('table-memory-budget', 'phase_budget_limit = 16; compiler_table_new(64, 8);', 'memory-budget'),
                ('table-byte-overflow', 'compiler_table_new(1073741824, 40);', 'table-byte-limit')]:
                ir = native(name, source(name, prefix + 'func main() i64 { ' + body + ' return 0; }\n'), execute=False)
                binary = output / name
                check(name + '-link', ['clang', '-O0', ir, '-o', binary])
                check(name, [binary], success=False, diagnostic=diagnostic)

        if args.group == 'targets':
            # Same positive and negative fixtures on LLVM native and direct Wasm.
            path = ROOT / 'test/suite/290_parameter_boundary.lang'
            native('target-native-positive', path)
            wasm_env = dict(env, LANGBE='wasm', LANGOS='wasm')
            wasm = output / 'target-positive.wasm'
            check('target-wasm-positive-emit', [compiler, path, '-o', wasm], run_env=wasm_env)
            check('target-wasm-positive-run', ['node', 'test/wasm_host.js', wasm])
            for backend, target_env in [('llvm', env), ('wasm', wasm_env)]:
                check('target-' + backend + '-negative', [compiler, 'test/suite/288_parameter_limit.lang', '-o', output / ('negative.' + backend)],
                      success=False, diagnostic='parameter limit exceeded (maximum 16)', run_env=target_env)
    finally:
        report = {'group': args.group, 'compiler_sha256': hashlib.sha256(compiler.read_bytes()).hexdigest(),
                  'seed_ir_sha256': hashlib.sha256((ROOT / 'bootstrap/current/compiler_linux.ll').read_bytes()).hexdigest(),
                  'rows': rows, 'full_scale_verdict': 'DEFERRED', 'self_compile_timing_verdict': 'DEFERRED',
                  'deferred_until': '2026-11-06T18:27:00-05:00'}
        (logs / (args.group + '.json')).write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
