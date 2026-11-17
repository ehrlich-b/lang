#!/usr/bin/env python3
"""Compare one portable flow program on native, LLVM-to-Wasm and direct Wasm."""
import argparse
from contextlib import nullcontext
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def run(argv, **kwargs):
    print('+', ' '.join(map(str, argv)), flush=True)
    return subprocess.run(argv, text=True, capture_output=True, **kwargs)


def compile_to(compiler, source, output, backend, target):
    env = dict(os.environ, LANGBE=backend, LANGOS=target)
    result = run([compiler, source, '-o', str(output)], env=env)
    print(result.stdout + result.stderr, end='')
    assert result.returncode == 0, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, help='retain generated proof artifacts here')
    options = parser.parse_args()
    if options.artifacts:
        options.artifacts.mkdir(parents=True, exist_ok=True)
    compiler = os.environ.get('COMPILER', 'out/lang_next')
    source = 'test/flow_wasm.lang'
    # TMPDIR can retain all generated artifacts outside the checkout.
    context = (nullcontext(options.artifacts) if options.artifacts else
               tempfile.TemporaryDirectory(prefix='flow-wasm-'))
    with context as tmp:
        root = Path(tmp)
        results = []
        native = 'macos' if sys.platform == 'darwin' else 'linux'
        for backend, target in [('llvm', native), ('llvm', 'wasm'), ('wasm', 'wasm')]:
            name = f'{backend}-{target}'
            output = root / (name + ('.ll' if backend == 'llvm' else '.wasm'))
            compile_to(compiler, source, output, backend, target)
            if target == native:
                executable = root / name
                linked = run(['clang', '-O2', str(output), '-o', str(executable)])
                command = [str(executable)]
            elif backend == 'llvm':
                executable = root / (name + '.wasm')
                linked = run(['clang', '-O2', '--target=wasm32-unknown-unknown', '-nostdlib',
                              '-Wl,--no-entry', '-Wl,--export-all', '-Wl,--allow-undefined',
                              '-Wl,-z,stack-size=8388608', str(output), '-o', str(executable)])
                command = ['node', 'test/wasm_host.js', str(executable)]
            else:
                linked = None
                command = ['node', 'test/wasm_host.js', str(output)]
            if linked is not None:
                print(linked.stdout + linked.stderr, end='')
                assert linked.returncode == 0, linked
            result = run(command)
            print(f'{name}: exit={result.returncode}, stdout={result.stdout!r}', flush=True)
            assert result.returncode == 42 and result.stdout == 'flow answer: 42\n', result
            results.append((result.returncode, result.stdout))
        assert len(set(results)) == 1
        # A portable profile must refuse the operation it cannot represent at
        # the user's yield, rather than silently weakening generator semantics.
        for backend, target in [('llvm', native), ('llvm', 'wasm'), ('wasm', 'wasm')]:
            for fixture, diagnostic in [('flow_portable_reject', 'yield expressions'),
                                        ('flow_portable_recursive_reject', 'recursive generator specialization')]:
                rejected = root / f'{fixture}-{backend}-{target}.wasm'
                source = f'test/{fixture}.lang'
                result = run([compiler, source, '-o', str(rejected)],
                             env=dict(os.environ, LANGBE=backend, LANGOS=target))
                print(result.stdout + result.stderr, end='')
                assert result.returncode == 1 and not rejected.exists(), result
                pattern = re.escape(source) + r':3:\d+: (?:error: )?' + diagnostic
                assert re.search(pattern, result.stderr), result.stderr
        # The existing effects reader still supports bidirectional yield/send.
        legacy = root / 'native-effects.ll'
        compile_to(compiler, 'example/flow/test_flow.lang', legacy, 'llvm', native)
        executable = root / 'native-effects'
        linked = run(['clang', '-O0', str(legacy), '-o', str(executable)])
        assert linked.returncode == 0, linked
        result = run([str(executable)])
        print(result.stdout + result.stderr, end='')
        assert result.returncode == 0 and 'FLOW PASS\n' in result.stdout, result
    print('flow native / LLVM-to-Wasm / direct Wasm: PASS')


if __name__ == '__main__':
    main()
