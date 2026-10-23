#!/usr/bin/env python3
"""Check local fixed-f32 array literals against independent IEEE-754 u32 bits.

Both integer inputs are hand-authored. Decimal tokens are supported only by
Lang; this test neither round-trips Lang ASTs nor adds decimal core syntax.
Requires actual Linux x86-64 execution and wasm32 execution through wasm_host.js.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test/f32_array_literals'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--expect-regression', action='store_true',
                        help='prove the pinned compiler emits rejected integer-array IR')
    args = parser.parse_args()
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64',
            'requires actual Linux x86-64 execution')
    base = args.evidence.resolve()
    require(base != ROOT and ROOT not in base.parents, 'evidence must be outside checkout')
    base.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='f32-', dir=base))
    compiler = args.compiler.resolve()
    expected = json.loads((FIXTURES / 'expected.json').read_text())
    cases = [('integers', 'lang'), ('integers', 'ast'), ('mixed', 'lang'), ('decimal', 'lang')]
    rows = []
    report = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  compiler=dict(path=str(compiler), sha256=digest(compiler)),
                  sources={str(p.relative_to(ROOT)): digest(p) for p in
                           [ROOT / 'src/codegen_llvm.lang', Path(__file__).resolve(),
                            ROOT / 'test/wasm_host.js', *sorted(FIXTURES.iterdir())] if p.is_file()},
                  expected_bits=expected, expect_regression=args.expect_regression,
                  targets=['x86_64-unknown-linux-gnu (native)',
                           'wasm32-unknown-unknown (LLVM to Wasm, Node host)'],
                  decimal_limit='Lang only; the core reader cannot parse decimal tokens',
                  commands=rows)

    def run(command, target, expected_exit=0):
        command = [str(x) for x in command]
        env = dict(os.environ, LANGBE='llvm', LANGOS=target, LANG_CACHE=str(out / 'cache'))
        for key in ('LANG_ROOT', 'LANG_LAYOUT_PROFILE'):
            env.pop(key, None)
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        n = len(rows)
        stdout, stderr = out / f'{n}.stdout', out / f'{n}.stderr'
        stdout.write_bytes(result.stdout)
        stderr.write_bytes(result.stderr)
        rows.append(dict(command=command, target=target, exit=result.returncode,
                         expected=expected_exit, stdout=str(stdout), stderr=str(stderr)))
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        if expected_exit is not None:
            require(result.returncode == expected_exit,
                    f'{command}: exit {result.returncode}, expected {expected_exit}; see {stderr}')
        return result

    # The Wasm host calls an i64 main; the C oracle itself uses its normal i32
    # result. This wrapper transports only the oracle status, never array bits.
    wrapper = out / 'wasm-main.ll'
    wrapper.write_text('declare i32 @f32_oracle_main()\n'
                       'define i64 @main(i64 %argc, i8* %argv, i8* %envp) {\n'
                       '  %r = call i32 @f32_oracle_main()\n'
                       '  %w = zext i32 %r to i64\n  ret i64 %w\n}\n')
    rejected = 0
    run([compiler, 'version'], 'linux')
    run(['clang', '--version'], 'linux')
    run(['node', '--version'], 'wasm')
    for target in ('linux', 'wasm'):
        for label, reader in cases:
            source = FIXTURES / f'{label}.{reader}'
            module = out / f'{target}-{label}-{reader}.ll'
            run([compiler, source, *(['--from-ast'] if reader == 'ast' else []), '-o', module], target)
            bits = [int(value, 16) for value in expected[label]]
            driver = out / f'{target}-{label}-{reader}.c'
            driver_text = ('#include <stdint.h>\nextern int64_t f32_bits(int64_t);\n'
                           'int main(void) {\n  static const uint32_t expected[] = {' +
                           ', '.join(f'0x{value:08x}u' for value in bits) + '};\n'
                           f'  for (int64_t i = 0; i < {len(bits)}; ++i)\n'
                           '    if ((uint64_t)f32_bits(i) != expected[i]) return 1;\n'
                           '  return 42;\n}\n')
            driver.write_text(driver_text)
            for opt in ('-O0', '-O2'):
                exe = out / f'{target}-{label}-{reader}{opt}'
                flags = [opt, '-std=c11']
                extra = []
                if target == 'wasm':
                    flags += ['--target=wasm32-unknown-unknown', '-ffreestanding', '-nostdlib',
                              '-Dmain=f32_oracle_main', '-Wl,--no-entry', '-Wl,--export-all',
                              '-Wl,--allow-undefined', '-Wl,-z,stack-size=8388608']
                    extra = [wrapper]
                else:
                    flags += ['--target=x86_64-unknown-linux-gnu']
                regression = args.expect_regression and label != 'decimal'
                result = run(['clang', *flags, module, driver, *extra, '-o', exe], target,
                             None if regression else 0)
                if regression:
                    require(result.returncode != 0 and b'integer constant must have integer type' in result.stderr,
                            f'{target}/{label}/{reader}/{opt}: missing pinned integer-array rejection')
                    rejected += 1
                    continue
                execute = lambda path: ['node', ROOT / 'test/wasm_host.js', path] if target == 'wasm' else [path]
                run(execute(exe), target, 42)
                if label == 'decimal':
                    # Exercise the real clang and runtime checks with broken
                    # IR and a one-bit error in an independent expected word.
                    malformed = out / f'{target}-malformed.ll'
                    text = module.read_text()
                    require('store float ' in text, 'missing float array store')
                    malformed.write_text(text.replace('store float ', 'store float BROKEN ', 1))
                    bad = run(['clang', *flags, malformed, driver, *extra, '-o', out / 'malformed'], target, None)
                    require(bad.returncode != 0, 'clang accepted malformed IR control')
                    wrong = out / f'{target}-wrong.c'
                    wrong.write_text(driver_text.replace('0x3fc00000u', '0x3fc00001u', 1))
                    wrong_exe = out / f'{target}-wrong{opt}'
                    run(['clang', *flags, module, wrong, *extra, '-o', wrong_exe], target)
                    run(execute(wrong_exe), target, 1)
                print(f'PASS {target} {reader} {label} {opt}: {len(bits)} exact u32 words')
    require(not args.expect_regression or rejected == 12, 'incomplete pinned regression coverage')
    report.update(status='PASS', rejected_integer_builds=rejected)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS f32 array literals:', out / 'report.json')


if __name__ == '__main__':
    main()
