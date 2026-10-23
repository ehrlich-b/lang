#!/usr/bin/env python3
"""Execute global f32 literal aggregates against frozen IEEE-754 bit words.

Integer Lang and core-reader inputs are hand-authored independently. Decimal
fixtures remain Lang-only: the existing core reader cannot parse decimal tokens.
Both native Linux x86-64 and LLVM-to-Wasm/Node must execute at O0 and O2.
Decimal cases include inexact values, halfway ties and a value just beyond a
tie that would round incorrectly through binary64, plus subnormal boundaries.
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
FIXTURES = ROOT / 'test/global_f32_arrays'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64',
            'requires actual Linux x86-64 execution')
    base = args.evidence.resolve()
    require(base != ROOT and ROOT not in base.parents, 'evidence must be outside checkout')
    base.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='global-f32-', dir=base))
    compiler = args.compiler.resolve()
    expected = json.loads((FIXTURES / 'expected.json').read_text())
    rows = []
    report = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  compiler=dict(path=str(compiler), sha256=digest(compiler)),
                  sources={str(p.relative_to(ROOT)): digest(p) for p in
                           [ROOT / 'src/codegen_llvm.lang', Path(__file__).resolve(),
                            ROOT / 'test/wasm_host.js', *sorted(FIXTURES.iterdir())] if p.is_file()},
                  expected_bits=expected, commands=rows,
                  targets=['native Linux x86-64', 'LLVM-to-Wasm/Node'],
                  decimal_limit='Lang only; the core reader cannot parse decimal tokens')

    def run(argv, target, expected_exit=0, diagnostic=None):
        argv = [str(x) for x in argv]
        env = dict(os.environ, LANGBE='llvm', LANGOS=target, LANG_CACHE=str(out / 'cache'))
        for key in ('LANG_ROOT', 'LANG_LAYOUT_PROFILE'):
            env.pop(key, None)
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=180)
        stdout, stderr = out / f'{len(rows)}.stdout', out / f'{len(rows)}.stderr'
        stdout.write_bytes(result.stdout)
        stderr.write_bytes(result.stderr)
        rows.append(dict(argv=argv, cwd=str(ROOT), target=target, exit=result.returncode,
                         expected=expected_exit, stdout=str(stdout), stderr=str(stderr)))
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        if expected_exit is not None:
            require(result.returncode == expected_exit,
                    f'{argv}: exit {result.returncode}, expected {expected_exit}; see {stderr}')
        if diagnostic:
            require(diagnostic.encode() in result.stderr, f'missing diagnostic: {diagnostic}; see {stderr}')
        return result

    wrapper = out / 'wasm-main.ll'
    wrapper.write_text('declare i32 @f32_oracle_main()\n'
                       'define i64 @main(i64 %argc, i8* %argv, i8* %envp) {\n'
                       '  %r = call i32 @f32_oracle_main()\n'
                       '  %w = zext i32 %r to i64\n  ret i64 %w\n}\n')
    run([compiler, 'version'], 'linux')
    run(['clang', '--version'], 'linux')
    run(['node', '--version'], 'wasm')
    positives = [p for p in sorted(FIXTURES.iterdir())
                 if p.suffix in ('.lang', '.ast') and not p.stem.startswith('invalid_')]
    negatives = sorted(FIXTURES.glob('invalid_*'))
    controls = []
    for target in ('linux', 'wasm'):
        for source in positives:
            label = source.stem
            module = out / f'{target}-{source.name}.ll'
            run([compiler, source, *(['--from-ast'] if source.suffix == '.ast' else []), '-o', module], target)
            bits = expected[label]
            driver = out / f'{target}-{source.name}.c'
            text = ('#include <stdint.h>\nextern int64_t f32_bits(int64_t);\n'
                    'int main(void) {\n  static const uint32_t expected[] = {' +
                    ', '.join('0x' + value + 'u' for value in bits) + '};\n'
                    f'  for (int64_t i = 0; i < {len(bits)}; ++i)\n'
                    '    if ((uint64_t)f32_bits(i) != expected[i]) return 1;\n'
                    '  return 42;\n}\n')
            driver.write_text(text)
            for opt in ('-O0', '-O2'):
                exe = out / f'{target}-{source.name}{opt}'
                flags = [opt, '-std=c11']
                extra = []
                if target == 'wasm':
                    flags += ['--target=wasm32-unknown-unknown', '-ffreestanding', '-nostdlib',
                              '-Dmain=f32_oracle_main', '-Wl,--no-entry', '-Wl,--export-all',
                              '-Wl,--allow-undefined', '-Wl,-z,stack-size=8388608']
                    extra = [wrapper]
                else:
                    flags += ['--target=x86_64-unknown-linux-gnu']
                execute = lambda path: ['node', ROOT / 'test/wasm_host.js', path] if target == 'wasm' else [path]
                run(['clang', *flags, module, driver, *extra, '-o', exe], target)
                run(execute(exe), target, 42)
                if source.name == 'integers.lang':
                    # Controls traverse the same assembler and runtime oracles.
                    malformed = out / f'{target}-malformed.ll'
                    ir = module.read_text()
                    require('@g = global [16 x float]' in ir, 'missing global f32 aggregate')
                    malformed.write_text(ir.replace('@g = global [16 x float]', '@g = global [16 x BROKEN]', 1))
                    result = run(['clang', *flags, malformed, driver, *extra, '-o', out / 'malformed'], target, None)
                    require(result.returncode != 0, 'clang accepted malformed-IR control')
                    wrong = out / f'{target}-wrong.c'
                    require('0x4b800002u' in text, 'missing frozen rounding-tie word')
                    wrong.write_text(text.replace('0x4b800002u', '0x4b800003u', 1))
                    wrong_exe = out / f'{target}-wrong{opt}'
                    run(['clang', *flags, module, wrong, *extra, '-o', wrong_exe], target)
                    run(execute(wrong_exe), target, 1)
                    controls.append(dict(target=target, opt=opt, malformed='rejected', wrong_bit='exit 1'))
                print(f'PASS {target} {source.name} {opt}: {len(bits)} exact u32 words')
        for source in negatives:
            module = out / f'{target}-{source.name}.ll'
            diagnostic = ('f32 global array element requires a numeric literal' if 'global' in source.stem else
                          'f32 array element requires a numeric literal or an explicit f32 value')
            if 'range' in source.stem:
                diagnostic = ('f32 array decimal literal is outside finite range' if 'decimal' in source.stem else
                              'f32 array integer literal is outside i64 range')
            run([compiler, source, *(['--from-ast'] if source.suffix == '.ast' else []), '-o', module],
                target, 1, diagnostic)
            require(not module.exists() or module.stat().st_size == 0, 'rejection published an invalid module')
            print(f'PASS {target} {source.name}: loud rejection')
    require(len(controls) == 4, 'incomplete negative controls')
    report.update(status='PASS', controls=controls, accepted_executions=len(positives) * 4,
                  compiler_rejections=len(negatives) * 2)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS global f32 arrays:', out / 'report.json')


if __name__ == '__main__':
    main()
