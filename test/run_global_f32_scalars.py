#!/usr/bin/env python3
"""Execute global f32 scalars against independent frozen IEEE-754 words.

Lang and handwritten core inputs cover integers and mutation. Decimal tokens
are Lang-only. Each fixture executes on native x86-64 and LLVM-to-Wasm/Node
at O0/O2; real assembler and wrong-bit controls must fail in both Python modes.
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
FIXTURES = ROOT / 'test/global_f32_scalars'


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
    out = Path(tempfile.mkdtemp(prefix='global-f32-scalars-', dir=base))
    compiler = args.compiler.resolve()
    expected = json.loads((FIXTURES / 'expected.json').read_text())
    rows = []
    report = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  python_optimized=not __debug__,
                  compiler=dict(path=str(compiler), sha256=digest(compiler)),
                  inputs={str(p.relative_to(ROOT)): digest(p) for p in
                          [ROOT / 'src/codegen_llvm.lang', Path(__file__).resolve(),
                           ROOT / 'test/wasm_host.js', *sorted(FIXTURES.iterdir())] if p.is_file()},
                  expected_bits=expected, commands=rows,
                  targets=['native Linux x86-64', 'LLVM-to-Wasm/Node'])

    def save():
        report['artifacts'] = {str(p.relative_to(out)): digest(p) for p in sorted(out.iterdir())
                               if p.is_file() and p.name != 'report.json'}
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')

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
                         expected=expected_exit, stdout=str(stdout), stderr=str(stderr),
                         stdout_sha256=digest(stdout), stderr_sha256=digest(stderr)))
        save()
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
    positives = [FIXTURES / name for name in expected if name.endswith(('.lang', '.ast'))]
    controls = []
    for target in ('linux', 'wasm'):
        for source in positives:
            module = out / f'{target}-{source.name}.ll'
            run([compiler, source, *(['--from-ast'] if source.suffix == '.ast' else []), '-o', module], target)
            bits = expected[source.name]
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

                def execute(path):
                    return ['node', ROOT / 'test/wasm_host.js', path] if target == 'wasm' else [path]

                run(['clang', *flags, module, driver, *extra, '-o', exe], target)
                run(execute(exe), target, 42)
                if source.name == 'integers.lang':
                    malformed = out / f'{target}-malformed.ll'
                    ir = module.read_text()
                    require('@g0 = global float' in ir, 'missing global f32 scalar storage')
                    malformed.write_text(ir.replace('@g0 = global float', '@g0 = global BROKEN', 1))
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
        for name, diagnostic in expected['rejections'].items():
            source = FIXTURES / name
            module = out / f'{target}-{name}.ll'
            run([compiler, source, *(['--from-ast'] if source.suffix == '.ast' else []), '-o', module],
                target, 1, diagnostic)
            require(not module.exists() or module.stat().st_size == 0, 'rejection published an invalid module')
            print(f'PASS {target} {name}: loud rejection')
    require(len(controls) == 4, 'incomplete negative controls')
    report.update(status='PASS', controls=controls, accepted_executions=len(positives) * 4,
                  compiler_rejections=len(expected['rejections']) * 2)
    save()
    print('PASS global f32 scalars:', out / 'report.json')


if __name__ == '__main__':
    main()
