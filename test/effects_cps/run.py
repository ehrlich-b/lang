#!/usr/bin/env python3
"""Run the effect suite and flow demo under selective CPS."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
COMPILER = str(Path(os.environ.get('COMPILER', 'out/lang')).resolve())
OUT = Path(os.environ.get('EFFECTS_CPS_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='effects-cps-')).resolve()
OUT.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, LANGBE='llvm', LANG_EFFECTS='cps', LANG_CACHE=str(OUT / 'cache'))
SUITE_MODES = [('O0', ['-O0']), ('O2', ['-O2'])]
QUALIFICATION_MODES = [SUITE_MODES[0], ('O1', ['-O1']), SUITE_MODES[1],
                       ('O2-lto', ['-O2', '-flto'] + ([] if sys.platform == 'darwin' else ['-fuse-ld=lld']))]
FLOW_OUTPUT = (b'sum_count(5)   = 10\n'
               b'sum_fib(10)    = 88\n'
               b'count_evens(10)= 5\n'
               b'drive_sum(4)   = 6\n'
               b'drive_sum(5)   = 10\n'
               b'FLOW PASS\n')
rows = []

def run(args, label, env=ENV):
    result = subprocess.run(args, env=env, capture_output=True, timeout=60)
    path = OUT / label
    path.parent.mkdir(parents=True, exist_ok=True)
    Path(str(path) + '.stdout').write_bytes(result.stdout)
    Path(str(path) + '.stderr').write_bytes(result.stderr)
    Path(str(path) + '.exit').write_text(f'{result.returncode}\n')
    return result


def emit(source, label, env=ENV):
    ir = OUT / (label + '.ll')
    result = run([COMPILER, source, '-o', str(ir)], label + '-emit', env)
    assert result.returncode == 0, result.stderr.decode(errors='replace')
    assert b'call void asm' not in ir.read_bytes(), 'assembly transfer in CPS module'
    assert b'__lang_effects_require_O0' not in ir.read_bytes(), 'CPS optimization refusal'
    return ir


def execute(source, expected, status=0, error=b'', *, modes=QUALIFICATION_MODES):
    name = Path(source).stem
    ir = emit(source, name)
    for mode, flags in modes:
        binary = OUT / f'{name}-{mode}'
        built = run([os.environ.get('CLANG', 'clang'), *flags, str(ir), '-o', str(binary)], f'{name}-{mode}-build')
        assert built.returncode == 0, built.stderr.decode(errors='replace')
        result = run([str(binary)], f'{name}-{mode}-run')
        assert result.returncode == status, (name, mode, result.returncode, result.stderr)
        assert result.stdout == expected, (name, mode, result.stdout, expected)
        assert result.stderr == error, (name, mode, result.stderr, error)
        rows.append({'source': source, 'mode': mode, 'exit': status, 'stdout': expected.decode(), 'verdict': 'PASS'})
        detail = expected.decode().strip() or error.decode().strip() or f'exit {status}'
        print(f'{source} {mode}: PASS ({detail})')


def effect_suite():
    suite = Path('test/suite')
    effect_syntax = re.compile(r'^\s*effect\s+\w+\s*\(|\bperform\s+\w+\s*\(|\bhandle\s*\{', re.M)
    for source in sorted(suite.glob('*.lang')):
        lines = source.read_text().splitlines()
        code = '\n'.join(line for line in lines if not line.lstrip().startswith('//'))
        if effect_syntax.search(code):
            marker = re.match(r'// expect:\s*(\d+)', lines[0])
            status = int(marker[1]) if marker else 0
            execute(str(source), b'', status, modes=SUITE_MODES)
    for source in sorted((suite / 'effects_cps').glob('*.lang')):
        execute(str(source), b'', modes=SUITE_MODES)
    execute('example/flow/test_flow.lang', FLOW_OUTPUT, modes=SUITE_MODES)


def native_comparison():
    for source in ['test/effects_cps/native.lang', 'test/effects_cps/mixed.lang']:
        name = Path(source).stem
        on = emit(source, name + '-on').read_text()
        off_env = dict(ENV)
        off_env.pop('LANG_EFFECTS', None)
        off_file = OUT / (name + '-off.ll')
        result = run([COMPILER, source, '-o', str(off_file)], name + '-off-emit', off_env)
        assert result.returncode == 0, result.stderr.decode(errors='replace')
        off = off_file.read_text()
        if name == 'native':
            assert on == off, 'effect-free module changed with the flag'
        else:
            pattern = r'^define [^\n]* @native_square\([^\n]*\) \{\n.*?^\}'
            assert re.search(pattern, on, re.M | re.S).group() == re.search(pattern, off, re.M | re.S).group(), 'native function changed in effectful module'
        rows.append({'source': source, 'verdict': 'PASS', 'native_ir': 'identical'})
        print(f'{name}: native IR identical with flag on/off')


def legacy_controls():
    off_env = dict(ENV)
    off_env.pop('LANG_EFFECTS', None)
    for name, expected in [('aggregate_alias', b'42\n'),
                           ('aggregate_cast_alias', None),
                           ('aggregate_field_alias', b'42\n'),
                           ('struct_alias', b'42\n'),
                           ('struct_field_alias', b'42\n'),
                           ('pointer_spill', b'22\n')]:
        ir = OUT / (name + '-legacy.ll')
        result = run([COMPILER, f'test/effects_cps/{name}.lang', '-o', str(ir)], name + '-legacy-emit', off_env)
        assert result.returncode == 0, result.stderr.decode(errors='replace')
        binary = OUT / (name + '-legacy')
        result = run([os.environ.get('CLANG', 'clang'), '-O0', str(ir), '-o', str(binary)], name + '-legacy-build', off_env)
        if expected is None:
            # Bare array casts are already unsupported by the legacy emitter.
            # Keep this negative input: CPS must reject before publishing IR.
            assert result.returncode != 0 and b"expected '[2 x i64]'" in result.stderr, result.stderr
            rows.append({'source': name, 'verdict': 'PASS', 'legacy_O0': 'unsupported array cast'})
            print(f'{name}: legacy array cast remains unsupported')
            continue
        assert result.returncode == 0, result.stderr.decode(errors='replace')
        result = run([str(binary)], name + '-legacy-run', off_env)
        assert (result.returncode, result.stdout, result.stderr) == (0, expected, b''), (name, result.stdout, result.stderr)
        rows.append({'source': name, 'verdict': 'PASS', 'legacy_O0': expected.decode()})
        print(f'{name}: legacy O0 control passed')
    for name, count in [('arity_missing', 0), ('arity_extra', 2)]:
        reject(f'test/effects_cps/{name}.lang',
               f"function 'worker' takes 1 argument, called with {count}".encode(),
               env=off_env, suffix='-legacy')


def reject(source, diagnostic, env=ENV, suffix=''):
    name = Path(source).stem + suffix
    output = OUT / (name + '.ll')
    result = run([COMPILER, source, '-o', str(output)], name + '-emit', env)
    assert result.returncode != 0 and diagnostic in result.stderr, (source, result.stderr)
    assert not output.exists(), 'refused core published an output'
    rows.append({'source': source, 'verdict': 'PASS', 'diagnostic': diagnostic.decode()})
    print(f'{name}: correctly refused')

parser = argparse.ArgumentParser(description=__doc__)
profile = parser.add_mutually_exclusive_group()
profile.add_argument('--qualification', action='store_true', help='run the CPS safety and IR fixtures')
profile.add_argument('--native-only', action='store_true', help='compare native IR with CPS on and off')
args = parser.parse_args()

try:
    if args.qualification:
        native_comparison()
        legacy_controls()
        for source, expected in [
            ('test/effects/two_performs.lang', b'500491\n'),
            ('test/effects/two_handlers.lang', b'2268\n'),
            ('test/effects_cps/state.lang', b'500491\n4\n'),
            ('test/effects_cps/pointer_spill.lang', b'22\n'),
            ('test/effects_cps/aggregate_region.lang', b'42\n'),
            ('test/effects_cps/struct_region.lang', b'42\n'),
            ('test/effects_cps/arity_valid.lang', b'42\n'),
            ('test/effects_cps/normal_return.lang', b'33\n'),
            ('test/effects_cps/abandon.lang', b'77\n'),
            ('test/effects_cps/nested.lang', b'340\n'),
            ('test/effects_cps/mixed.lang', b''),
            ('test/effects_cps/reentry.lang', b''),
            ('test/effects_cps/shadow.lang', b''),
            ('test/effects_cps/control.lang', b''),
            ('test/effects_cps/flow.lang', b''),
        ]:
            execute(source, expected)
        execute('test/effects_cps/unhandled.lang', b'', 1, b'E_UNHANDLED\n')
        reject('test/effects_cps/non_tail.lang', b'tail position')
        reject('test/effects_cps/escape.lang', b'continuation may only occur')
        reject('test/effects_cps/address_escape.lang', b'unproved escape lifetime')
        for source in ['aggregate_alias', 'aggregate_cast_alias', 'aggregate_field_alias',
                       'struct_alias', 'struct_field_alias']:
            reject(f'test/effects_cps/{source}.lang', b'unproved escape lifetime')
        for name, count in [('arity_missing', 0), ('arity_extra', 2)]:
            reject(f'test/effects_cps/{name}.lang',
                   f"function 'worker' takes 1 argument, called with {count}".encode())
        reject('test/effects_cps/callback.lang', b'native/foreign call boundary')
    elif args.native_only:
        native_comparison()
    else:
        effect_suite()
except (AssertionError, subprocess.TimeoutExpired) as exc:
    rows.append({'verdict': 'FAIL', 'error': str(exc)})
    (OUT / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(f'CPS semantics: FAIL: {exc}', file=sys.stderr)
    sys.exit(1)
(OUT / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
print('CPS semantics: PASS')
