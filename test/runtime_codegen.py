#!/usr/bin/env python3
"""Execute pointer lowering, reader, and cross-target regression witnesses."""
import argparse
import difflib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--baseline-compiler', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('evidence must be outside the checkout')
    output.mkdir(parents=True, exist_ok=True)
    compiler = args.compiler.resolve()
    baseline = args.baseline_compiler.resolve()
    records = []

    def run(argv, *, env=None, expected=0, diagnostic=None):
        result = subprocess.run(list(map(str, argv)), cwd=ROOT, env=env,
                                capture_output=True, timeout=180)
        record = {'command': list(map(str, argv)), 'exit_code': result.returncode,
                  'stdout': result.stdout.decode(errors='replace'),
                  'stderr': result.stderr.decode(errors='replace')}
        records.append(record)
        (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
        print(json.dumps(record), flush=True)
        if diagnostic:
            assert result.returncode != 0 and diagnostic in result.stderr, record
        else:
            assert result.returncode == expected, record
        return result

    native_env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LANG_CACHE=str(output / 'cache'))
    fixture = 'test/suite/301_pointer_induction.lang'
    for label, tool in [('base', baseline), ('candidate', compiler)]:
        ir = output / (label + '.ll')
        run([tool, fixture, '-o', ir], env=native_env)
        for opt in ['-O0', '-O2']:
            binary = output / (label + opt)
            run(['clang', opt, ir, '-o', binary])
            run([binary], expected=42)
    text = (output / 'candidate.ll').read_text()
    # Byte, bool, i64, double and complete Pair storage have native GEP strides.
    for spelling in ['getelementptr i8,', 'getelementptr i1,', 'getelementptr i64,',
                     'getelementptr double,', 'getelementptr [16 x i8],']:
        assert spelling in text, spelling
    assert 'nsw' not in text and 'nuw' not in text
    (output / 'native-ir.diff').write_text(''.join(difflib.unified_diff(
        (output / 'base.ll').read_text().splitlines(True), text.splitlines(True),
        fromfile='base', tofile='candidate')))
    run(['clang', '-O2', '-c', '-target', 'arm64-apple-macosx', output / 'candidate.ll',
         '-o', output / 'pointer-arm64.o'])
    # Exercise an actual expanding reader using the same seed-built compiler.
    reader_ir = output / 'reader.ll'
    run([compiler, 'test/suite/299_shadow_minilisp.lang', '-o', reader_ir], env=native_env)
    run(['clang', '-O2', reader_ir, '-o', output / 'reader'])
    reader = run([output / 'reader'])
    assert reader.stdout == b'42\n'
    wasm_env = dict(native_env, LANGOS='wasm')
    wasm_ir = output / 'pointer-wasm.ll'
    run([compiler, fixture, '-o', wasm_ir], env=wasm_env)
    run(['clang', '--target=wasm32-unknown-unknown', '-nostdlib', '-O2',
         '-Wl,--no-entry', '-Wl,--export-all', '-Wl,--allow-undefined',
         wasm_ir, '-o', output / 'pointer.wasm'])
    run(['node', 'test/wasm_host.js', output / 'pointer.wasm'], expected=42)
    run([compiler, 'test/suite/270_i128_basic.lang', '-o', output / 'reject.ll'],
        env=wasm_env, diagnostic=b'numeric: unknown or unsupported declared type')
    print('Native O0/O2, reader, arm64 object, Wasm execution and rejection: PASS')


if __name__ == '__main__':
    main()
