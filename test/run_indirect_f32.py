#!/usr/bin/env python3
"""Check indirect f32 storage against handwritten frozen words on native/Wasm.

The independent Lang and core fixtures exercise aliases, local/global addresses,
pointer parameters and exact values. Deliberate IR width and rounded-bit faults
must fail real clang/execution checks. All checks remain active under Python -O.
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
FIXTURES = ROOT / 'test/indirect_f32'


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
    out = Path(tempfile.mkdtemp(prefix='indirect-f32-', dir=base))
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
        command_inputs = {}
        for arg in argv:
            path = Path(arg)
            path = path if path.is_absolute() else ROOT / path
            if path.is_file():
                command_inputs[str(path.resolve())] = digest(path)
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=180)
        stdout, stderr = out / f'{len(rows)}.stdout', out / f'{len(rows)}.stderr'
        stdout.write_bytes(result.stdout)
        stderr.write_bytes(result.stderr)
        rows.append(dict(argv=argv, cwd=str(ROOT), target=target, exit=result.returncode,
                         expected=expected_exit, inputs=command_inputs, stdout=str(stdout), stderr=str(stderr),
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
            text = ('#include <stdint.h>\nextern int64_t f32_bits(int64_t);\nextern int64_t i64_control(void);\n'
                    'int main(void) {\n  static const uint32_t expected[] = {' +
                    ', '.join('0x' + value + 'u' for value in bits) + '};\n'
                    f'  for (int64_t i = 0; i < {len(bits)}; ++i)\n'
                    '    if ((uint64_t)f32_bits(i) != expected[i]) return 1;\n'
                    f'  if (i64_control() != {expected["i64_control"]}) return 2;\n'
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
                if source.name == 'roundtrip.lang':
                    ir = module.read_text()
                    require('ptrtoint float* @cell' in ir, 'global address has wrong type/scope')
                    require('to float*' in ir and '= load float, float*' in ir,
                            'missing typed indirect f32 operations')
                    faults = {
                        'store-width': ('store float 0x3FB99999A0000000',
                                        'store i64 0x3FB99999A0000000',
                                        'floating point constant invalid for type'),
                        'load-width': ('= load float, float* %t', '= load i64, i64* %t',
                                       "defined with type 'i64' but expected 'float'"),
                    }
                    for fault, (before, after, diagnostic) in faults.items():
                        require(before in ir, f'missing {fault} control anchor')
                        malformed = out / f'{target}-{fault}{opt}.ll'
                        malformed.write_text(ir.replace(before, after, 1))
                        result = run(['clang', *flags, malformed, driver, *extra,
                                      '-o', out / f'{target}-{fault}{opt}'],
                                     target, None, diagnostic)
                        require(result.returncode != 0, f'clang accepted {fault} control')
                    before = 'store float 0x4170000040000000'
                    require(before in ir, 'missing rounded-tie store control anchor')
                    wrong = out / f'{target}-wrong-bit{opt}.ll'
                    wrong.write_text(ir.replace(before, 'store float 0x4170000060000000', 1))
                    wrong_exe = out / f'{target}-wrong-bit{opt}'
                    run(['clang', *flags, wrong, driver, *extra, '-o', wrong_exe], target)
                    run(execute(wrong_exe), target, 1)
                    controls.append(dict(target=target, opt=opt, store_width='clang rejected',
                                         load_width='clang rejected', wrong_rounded_bit='exit 1'))
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
    print('PASS indirect f32:', out / 'report.json')


if __name__ == '__main__':
    main()
