#!/usr/bin/env python3
"""Compare the candidate with a legacy compiler on the same source graph."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
os.chdir(root)
compiler = str(Path(os.environ.get('COMPILER', 'out/lang_next')).resolve())
base = str(Path(os.environ['BASE_COMPILER']).resolve())
evidence = Path(os.environ.get('EFFECTS_LEGACY_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='effects-legacy-')).resolve()
evidence.mkdir(parents=True, exist_ok=True)
programs = sorted(p for p in Path('test/suite').glob('*.lang')
                  if re.search(r'^\s*effect\s|\bperform\s|\bhandle\s*\{', p.read_text(), re.M))
programs += [Path('test/effects/two_performs.lang'), Path('test/effects/two_handlers.lang'), Path('test/effects_o2_twice.lang')]
programs += sorted(Path('test/effects_cps').glob('*.lang'))

arity = {'arity_missing': 0, 'arity_extra': 2}
refusals = dict.fromkeys(
    ('address_escape', 'aggregate_alias', 'aggregate_cast_alias',
     'aggregate_field_alias', 'struct_alias', 'struct_field_alias'),
    b'unproved escape lifetime',
)
refusals.update(non_tail=b'tail position', escape=b'continuation may only occur',
                callback=b'native/foreign call boundary')
# These cases have independent CPS oracles because legacy effects did not
# implement their semantics reliably at any optimization level.
cps_answers = {
    'control': (0, b'', b''),
    'nested': (0, b'340\n', b''),
    'normal_return': (0, b'33\n', b''),
    'reentry': (0, b'', b''),
    'unhandled': (1, b'', b'E_UNHANDLED\n'),
}
legacy_globals = (
    b'@__handler_set = internal global i64 0\n'
    b'@__handler_rbp = internal global i64 0\n'
    b'@__handler_rsp = internal global i64 0\n'
    b'@__handler_addr = internal global i64 0\n'
    b'@__effect_value = internal global i64 0\n'
    b'@__continuation_ptr = internal global i8* null\n'
    b'@__effect_name_ptr = internal global i8* null\n'
    b'@__effect_name_len = internal global i64 0\n'
    b'@__resume_value = internal global i64 0\n\n'
)


def run(args, directory, stage, env=None):
    result = subprocess.run(args, env=env, capture_output=True, timeout=60)
    (directory / f'{stage}.stdout').write_bytes(result.stdout)
    (directory / f'{stage}.stderr').write_bytes(result.stderr)
    (directory / f'{stage}.exit').write_text(f'{result.returncode}\n')
    return result


def behavior(ir, opt):
    directory = ir.parent
    binary = directory / 'program'
    built = run([os.environ.get('CLANG', 'clang'), opt, ir, '-o', binary], directory, 'link')
    assert built.returncode == 0, (ir, built.stderr)
    result = run([binary], directory, 'run')
    return result.returncode, result.stdout, result.stderr


rows = []
for source in programs:
    name = source.stem
    irs = {}
    diagnostics = {}
    for label, executable in [('base', base), ('candidate', compiler)]:
        directory = evidence / name / label
        directory.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(directory / 'cache'))
        ir = directory / 'program.ll'
        ir.unlink(missing_ok=True)
        result = run([executable, source, '-o', ir], directory, 'compiler', env)
        if name in arity or (label == 'candidate' and name in refusals):
            expected = refusals.get(name) or f"function 'worker' takes 1 argument, called with {arity[name]}".encode()
            assert result.returncode != 0 and expected in result.stderr, (source, label, result.stderr)
            assert not ir.exists(), (source, label, 'refused core published IR')
            diagnostics[label] = result.stderr.removesuffix(b'error: compilation failed\n')
        else:
            assert result.returncode == 0, (source, label, result.stderr)
            irs[label] = ir

    if name in arity:
        assert diagnostics['base'] == diagnostics['candidate'], (source, diagnostics)
        kind = 'matching arity diagnostic'
    elif name in refusals:
        kind = 'scoped CPS refusal'
    else:
        if name == 'native':
            baseline = irs['base'].read_bytes().replace(legacy_globals, b'', 1)
            assert irs['candidate'].read_bytes() == baseline, f'native IR differs for {source}'
        expected = cps_answers.get(name)
        if expected is None:
            expected = behavior(irs['base'], '-O0')
        actual = behavior(irs['candidate'], '-O2')
        assert actual == expected, (source, actual, expected)
        kind = 'CPS runtime oracle' if name in cps_answers else 'matching legacy behavior'
    candidate = diagnostics.get('candidate')
    if candidate is None:
        candidate = irs['candidate'].read_bytes()
    rows.append({'source': str(source), 'sha256': hashlib.sha256(candidate).hexdigest(),
                 'kind': kind, 'verdict': 'PASS'})
    print(f'{source}: {kind}')
(evidence / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
print(f'Legacy comparison: PASS ({len(rows)} programs)')
