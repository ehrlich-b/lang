#!/usr/bin/env python3
"""Native hand-lowered contract witnesses; all output lives outside the checkout.

Run from the repository root. Override EFFECTS_EVIDENCE_DIR/EFFECTS_BUILD_DIR to
select external output directories. No compiler feature is enabled by this test.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
EVIDENCE = Path(os.environ.get('EFFECTS_EVIDENCE_DIR', REPO.parent / 'evidence')).resolve()
BUILD = Path(os.environ.get('EFFECTS_BUILD_DIR', EVIDENCE.parent / 'scratch/effects-witness')).resolve()
for directory in (EVIDENCE, BUILD):
    if directory == REPO or REPO in directory.parents:
        sys.exit('REFUSE: evidence and build directories must be outside the checkout')
    directory.mkdir(parents=True, exist_ok=True)
COMMANDS, RESULTS = [], []
CLANG = os.environ.get('CLANG', shutil.which('clang'))
OPT = os.environ.get('OPT', shutil.which('opt'))
LLVM_AS = os.environ.get('LLVM_AS', shutil.which('llvm-as'))
LLD = os.environ.get('LLD', shutil.which('ld.lld'))
SYSTEM, MACHINE = platform.system(), platform.machine()


def command(args, *, build=False, expected=0):
    args = [str(x) for x in args]
    args = ['nice', '-n', '10', *args]
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=90)
    COMMANDS.append(dict(argv=args, exit=p.returncode, expected_exit=expected,
                         stdout=p.stdout, stderr=p.stderr))
    if p.returncode != expected:
        raise RuntimeError(f'command exited {p.returncode}, wanted {expected}: {args}\n{p.stderr}\n{p.stdout}')
    return p.stdout


def work(n, bias=100):
    a, b = n*3, n+7
    c = a+bias
    d = a*b+c
    e = d+bias
    f = e-a+b
    g = f*2+100
    return a+b*10+c*100+d*1000+e*3+f*7+g*11

def step(n, bias=100):
    p = n*11
    q = p+bias
    s = p+q*2
    t = s+bias
    return p+q*3+s*5+t*7

CASES = [
    ('two_perform', [1], 500491, 4),
    ('changed_inputs', [2], 621238, 4),
    ('two_handlers', [3], 22682676, 8),
    ('nested_nonmatching', [4], 254, 2),
    ('multiple_effectful_functions', [5], 1016, 1),
    ('reentrant_clause', [6], 129, 3),
    ('indirect_call', [7], 320288, 2),
    ('abandon_cleanup_order', [8], 77, 1),
    ('escape_after_region', [9], 'E_ESCAPE', None),
    ('double_resume_live_region', [10], 'E_USED', None),
    ('unhandled_call_before_install', [11], 'E_UNHANDLED', None),
    ('return_clause_nonidentity', [12], 33, 1),
    ('native_leaf_then_perform', [13], 24, 1),
    ('foreign_callback_refusal', [14], 'E_FOREIGN_SUSPEND', None),
    ('indirect_abi_refusal', [15], 'E_INDIRECT_ABI', None),
    ('resume_reinstalls_inner_handler', [16], 330, 2),
]
for seed in [-3, 0, 2, 5, 8, 11]:
    CASES.append((f'indirect_seed_{seed}', [17, seed], work(seed) if seed & 1 else step(seed), 2))

def exit_oracle(mode):
    """Direct source control; no events, frame IDs, dispatcher or prompt logic."""
    i, total, evals = 0, 0, 0
    while i < 4:
        i += 1
        if mode in (18, 19):
            evals += 1
            return 40 + evals
        total += i
        if mode in (20, 22):
            break
        continue
    return i * 100 + total

def flow_return_oracle(n):
    for x in range(n):
        if x == 3:
            return x
    return 9000

for mode, name in enumerate(['clause_return', 'body_return', 'clause_break',
                             'clause_continue', 'body_break', 'body_continue'], 18):
    CASES.append((name, [mode], exit_oracle(mode),
                  0 if mode in (19, 22, 23) else 4 if mode == 21 else 1))
CASES.extend([
    ('flow_for_body_return', [24], flow_return_oracle(6), 4),
    ('flow_sum_count_by_reference', [25], sum(range(5)), 5),
    ('native_nested_dispatcher', [26], ((10 + 20 + 1) * 2 + 3) + 100, 2),
    ('nested_dispatcher_no_outward_lookup', [27], 'E_UNHANDLED', None),
    ('nested_dispatcher_inherits_foreign_depth', [28], 'E_FOREIGN_SUSPEND', None),
])
# Independent exact frame-finalization order, including already consumed clauses.
TRACES = {
    18: [5, 4, 3, 2, 1], 19: [4, 3, 2, 1], 20: [5, 4, 3, 2, 1],
    21: [5, 4, 3, 8, 7, 6, 11, 10, 9, 14, 13, 12, 2, 1],
    22: [4, 3, 2, 1], 23: [4, 3, 6, 5, 8, 7, 10, 9, 2, 1],
    24: [4, 5, 6, 7, 3, 2, 1], 25: [4, 5, 6, 7, 8, 3, 2, 1],
    26: [6, 5, 4, 7, 3, 2, 1], 27: [4, 3, 2, 1], 28: [5, 4, 3, 2, 1],
}

def check(binary, profile):
    for name, args, value, effects in CASES:
        negative = isinstance(value, str)
        output = command([binary, *map(str, args)], expected=64 if negative else 0).strip()
        observed = output
        if args[0] in TRACES:
            output, trace = output.split(' trace=')
            if list(map(int, trace.split(','))) != TRACES[args[0]]:
                raise RuntimeError(f'{profile}/{name}: wrong cleanup order: {observed}')
        if negative:
            good = re.fullmatch(re.escape(value) + r' cleanup=(\d+)/\1', output)
        else:
            good = re.fullmatch(str(value) + f' effects={effects}' + r' cleanup=(\d+)/\1 native=(\d+)', output)
            if good and int(good.group(2)) != (1 if name in ('native_leaf_then_perform', 'native_nested_dispatcher') else 0):
                good = False
        if not good:
            raise RuntimeError(f'{profile}/{name}: unexpected output {output!r}')
        RESULTS.append(dict(profile=profile, case=name, status='PASS', output=observed,
                            expected_exit=64 if negative else 0, exit=COMMANDS[-1]['exit']))

start = time.monotonic()
status = 'FAIL'
error_message = None
tool_versions = {}
try:
    if (SYSTEM, MACHINE) not in [('Linux', 'x86_64'), ('Darwin', 'arm64')]:
        raise RuntimeError('requires native Linux x86-64 or macOS arm64')
    required = [('clang', CLANG), ('opt', OPT), ('llvm-as', LLVM_AS)]
    if SYSTEM == 'Linux':
        required.append(('lld', LLD))
    if not all(exe for _, exe in required):
        raise RuntimeError('clang, opt, llvm-as and a native full-LTO linker are required')
    tool_versions = {name: command([exe, '--version']) for name, exe in required}
    majors = [re.search(r'version (\d+)', tool_versions[name]).group(1)
              for name in ('clang', 'opt', 'llvm-as')]
    if len(set(majors)) != 1:
        raise RuntimeError('clang/opt/llvm-as must have matching LLVM major versions')
    target = command([CLANG, '-dumpmachine']).strip()
    if SYSTEM == 'Linux' and not target.startswith('x86_64'):
        raise RuntimeError('clang must target the native x86-64 host')
    sources = ['machine.c', 'fixtures.c', 'foreign.c', 'control.c']
    flags = ['-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic']
    outward_expected = 'outward_clause_resume=790 cleanup=5/5\noutward_clause_abort=77 cleanup=5/5\n'

    def auxiliary(profile, compiler_flags, ir_source=ROOT / 'contract.ll'):
        ir_binary = BUILD / ('ir-' + profile)
        command([CLANG, *compiler_flags, ir_source, ROOT / 'ir_driver.c', '-o', ir_binary], build=True)
        output = command([ir_binary])
        if output != '340 checked-invalid-pc\n':
            raise RuntimeError(f'{profile}/minimal_ir: {output!r}')
        RESULTS.append(dict(profile=profile, case='minimal_ir', status='PASS', output=output.strip(), exit=0, expected_exit=0))
        outward = BUILD / ('outward-' + profile)
        command([CLANG, *flags, *compiler_flags, 'machine.c', 'independent_outward.c', '-o', outward], build=True)
        output = command([outward])
        if output != outward_expected:
            raise RuntimeError(f'{profile}/outward: {output!r}')
        for line in output.splitlines():
            RESULTS.append(dict(profile=profile, case=line.split('=')[0], status='PASS', output=line, exit=0, expected_exit=0))

    for level in ['O0', 'O1', 'O2']:
        binary = BUILD / level
        command([CLANG, *flags, f'-{level}', *sources, '-o', binary], build=True)
        check(binary, level)
        auxiliary(level, [f'-{level}'])

    # Every translation unit is bitcode. Retain the linker's native LTO object.
    lto = BUILD / 'full-lto'
    lto.mkdir(exist_ok=True)
    objects = []
    for source in sources:
        obj = lto / (source + '.o')
        command([CLANG, *flags, '-O2', '-flto=full', '-c', source, '-o', obj], build=True)
        if obj.read_bytes()[:4] not in (b'BC\xc0\xde', b'\xde\xc0\x17\x0b'):
            raise RuntimeError(f'not LLVM bitcode: {obj}')
        objects.append(obj)
    if SYSTEM == 'Linux':
        lto_flags = ['-O2', '-flto=full', f'--ld-path={LLD}', '-Wl,--save-temps']
        native_lto_object = lto / 'probe.lto.o'
    else:
        liblto = Path(CLANG).resolve().parent.parent / 'lib/libLTO.dylib'
        if not liblto.exists():
            raise RuntimeError('matching libLTO.dylib required; no downgrade from full LTO')
        lto_flags = ['-O2', '-flto=full', f'-Wl,-lto_library,{liblto}']
        native_lto_object = lto / 'linked.o'
    link_flags = lto_flags + ([f'-Wl,-object_path_lto,{native_lto_object}'] if SYSTEM == 'Darwin' else [])
    command([CLANG, *link_flags, *objects, '-o', lto / 'probe'], build=True)
    if not native_lto_object.exists():
        raise RuntimeError('linker did not retain LTO-generated native object')
    if SYSTEM == 'Linux' and native_lto_object.read_bytes()[:4] != b'\x7fELF':
        raise RuntimeError('LTO output is not a native ELF object')
    check(lto / 'probe', 'full-LTO-O2')
    auxiliary('full-LTO-O2', lto_flags)

    # Run the new-pass-manager O2 pipeline, verifying after every pass.
    pipeline = BUILD / 'pipeline'
    pipeline.mkdir(exist_ok=True)
    objects = []
    for source in sources:
        raw, optimized, obj = [pipeline / (source + ext) for ext in ('.ll', '.opt.ll', '.o')]
        command([CLANG, *flags, '-O0', '-Xclang', '-disable-O0-optnone', '-S', '-emit-llvm', source, '-o', raw], build=True)
        ir_text = raw.read_text()
        if re.search(r'\b(optnone|returns_twice|callbr|indirectbr|blockaddress|asm)\b', ir_text):
            raise RuntimeError(f'forbidden control escape or optimizer masking in {source}')
        command([LLVM_AS, raw, '-o', pipeline / (source + '.bc')], build=True)
        command([OPT, '-passes=default<O2>', '-verify-each', '-S', raw, '-o', optimized], build=True)
        command([CLANG, '-O2', '-c', optimized, '-o', obj], build=True)
        objects.append(obj)
    ir_optimized = pipeline / 'contract.opt.ll'
    # opt needs the native data layout before folding aggregate field offsets.
    ir_native = pipeline / 'contract.native.ll'
    command([CLANG, '-O0', '-S', '-emit-llvm', 'contract.ll', '-o', ir_native], build=True)
    command([LLVM_AS, ir_native, '-o', pipeline / 'contract.bc'], build=True)
    command([OPT, '-passes=default<O2>', '-verify-each', '-S', ir_native, '-o', ir_optimized], build=True)
    command([CLANG, *objects, '-o', pipeline / 'probe'], build=True)
    check(pipeline / 'probe', 'opt-default-O2-verify-each')
    auxiliary('opt-default-O2-verify-each', ['-O2'], ir_optimized)
    fixture_ir = (pipeline / 'fixtures.c.ll').read_text()
    match = re.search(r'define internal .*? @work\(.*?^}', fixture_ir, re.M | re.S)
    if not match:
        raise RuntimeError('cannot extract work IR witness')
    (EVIDENCE / 'work-emitted.txt').write_text(match.group(0) + '\n')
    sanitized = BUILD / 'sanitized'
    sanitizer_flags = ['-O1', '-fsanitize=address,undefined', '-fno-sanitize-recover=all']
    command([CLANG, *flags, *sanitizer_flags, *sources, '-o', sanitized], build=True)
    check(sanitized, 'ASan-UBSan-O1')
    auxiliary('ASan-UBSan-O1', sanitizer_flags)
    # Keep the original O2-sanitized outward regression as well.
    auxiliary('ASan-UBSan-O2', ['-O2', '-fsanitize=address,undefined', '-fno-sanitize-recover=all'])
    status = 'PASS'
except Exception as error:
    error_message = str(error)
    print(error_message, file=sys.stderr)
finally:
    receipt = dict(status=status, error=error_message, design_baseline='480e61e',
                   head=command(['git', '-C', REPO, 'rev-parse', 'HEAD']).strip(),
                   platform=platform.platform(), system=SYSTEM, machine=MACHINE,
                   tools=tool_versions, duration_seconds=round(time.monotonic()-start, 3),
                   tests=len(RESULTS), results=RESULTS,
                   inputs={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir()
                           if p.is_file() and p.suffix in ('.c', '.h', '.ll', '.py', '.lang')})
    (EVIDENCE / 'witness.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (EVIDENCE / 'commands.json').write_text(json.dumps(COMMANDS, indent=2) + '\n')
    (EVIDENCE / 'summary.tsv').write_text('profile\tcase\tstatus\toutput\n' + ''.join(
        '\t'.join(str(r[k]) for k in ('profile','case','status','output'))+'\n' for r in RESULTS))
print(f'{status}: {len(RESULTS)} native checks; receipt: {EVIDENCE / "witness.json"}')
sys.exit(0 if status == 'PASS' else 1)
