#!/usr/bin/env python3
"""Require realistic emitter mutations to fail the independent integer oracle."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='numeric-mutations-', dir=args.output)).resolve()
    compiler = (ROOT / 'out/lang_next').resolve()
    assert compiler.is_file(), 'run make build first'
    mutations = [
        ('signedness', 'src/codegen_llvm.lang',
         'if integer_type_signed(integer_expr_src(expr)) != 0 { llvm_emit_str("s"); }',
         'if integer_type_signed(integer_expr_src(expr)) == 0 { llvm_emit_str("s"); }',
         'oracle mismatch llvm'),
        ('conversion', 'src/codegen_wasm.lang',
         'wasm_integer_normalize(integer_expr_dst(expr), out);',
         'wasm_integer_normalize(integer_expr_src(expr), out);',
         'oracle mismatch wasm'),
    ]
    for name, file, before, after, expected_failure in mutations:
        checkout = directory / name
        subprocess.run(['git', 'clone', '--shared', '--quiet', str(ROOT), str(checkout)], check=True)
        source = checkout / file
        text = source.read_text()
        assert text.count(before) == 1, f'ambiguous mutation: {name}'
        source.write_text(text.replace(before, after))
        with (directory / (name + '-build.txt')).open('w') as log:
            subprocess.run(['make', 'build', f'LANG={compiler}'], cwd=checkout,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=240)
        result = subprocess.run(['python3', 'test/run_numeric.py', 'oracle',
                                 '--compiler', 'out/lang_next', '--output', str(directory / (name + '-oracle'))],
                                cwd=checkout, capture_output=True, timeout=180)
        (directory / (name + '-oracle.stdout')).write_bytes(result.stdout)
        (directory / (name + '-oracle.stderr')).write_bytes(result.stderr)
        assert result.returncode != 0, f'{name} mutation survived'
        assert expected_failure.encode() in result.stderr, 'mutation failed for an unrelated reason: ' + result.stderr.decode()
        print(f'PASS {name}: unchanged independent oracle rejected executable mutant; evidence {directory}', flush=True)
    obligations = (ROOT / 'docs/NUMERIC.md').read_text()
    for obligation in ('Layout phase L remains blocked', 'overflow', 'floating-point', 'divide-by-zero'):
        assert obligation in obligations, f'missing deferred N obligation: {obligation}'


if __name__ == '__main__':
    main()
