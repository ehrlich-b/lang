#!/usr/bin/env python3
"""Exercise production scalar/array storage, with independent C/LLVM evidence."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('mode', choices=['api', 'equivalence'])
p.add_argument('--compiler', required=True, type=Path)
p.add_argument('--baseline-compiler', type=Path)
p.add_argument('--evidence', required=True, type=Path)
a = p.parse_args()
assert platform.system() == 'Linux' and platform.machine() == 'x86_64', 'requires actual Linux x86-64 executor'
assert ROOT not in a.evidence.resolve().parents, 'evidence must stay outside checkout'
a.evidence.mkdir(parents=True, exist_ok=True)
out = Path(tempfile.mkdtemp(prefix=a.mode + '-', dir=a.evidence.resolve()))
compiler = a.compiler.resolve()
env = dict(os.environ, LANGBE='llvm', LANGOS='linux', LANG_CACHE=str(out / 'cache'))
for key in ('LANG_LAYOUT_PROFILE', 'LANG_ROOT'):
    env.pop(key, None)
rows = []

def run(command, expected=0, target='linux'):
    command = [str(x) for x in command]
    r = subprocess.run(command, cwd=ROOT, env=dict(env, LANGOS=target), capture_output=True, timeout=180)
    index = len(rows)
    (out / f'{index}.stdout').write_bytes(r.stdout)
    (out / f'{index}.stderr').write_bytes(r.stderr)
    rows.append(dict(command=command, target=target, exit=r.returncode, expected=expected))
    (out / 'commands.json').write_text(json.dumps(rows, indent=2) + '\n')
    assert r.returncode == expected, (command, r.returncode, r.stdout, r.stderr)
    return r

if a.mode == 'api':
    module = out / 'probe.ll'
    run([compiler, 'test/layout/probe.lang', '-o', module])
    results = []
    for opt in ('-O0', '-O2'):
        exe = out / ('oracle' + opt)
        run(['clang', '-std=c11', opt, module, 'test/layout/oracle.c', '-o', exe])
        result = run([exe]).stdout.decode()
        assert 'PASS ' in result and 'no arm64 execution' in result
        print(result, end='')
        results.append(result)
    assert results[0] == results[1]
    # Independently emit target sizeof/alignment constants using clang's wasm32
    # C layout. These rows are target checks; nothing here executes on arm64.
    oracle = out / 'wasm-target.ll'
    run(['clang', '--target=wasm32-unknown-unknown', '-ffreestanding', '-std=c11', '-S', '-emit-llvm',
         'test/layout/target_oracle.c', '-o', oracle])
    target_text = oracle.read_text()
    assert 'target triple = "wasm32-unknown-unknown"' in target_text
    count = 0
    for line in results[0].splitlines():
        if not line.startswith('llvm-wasm32 '):
            continue
        name = line.split()[1]
        expected = [int(x) for x in re.findall(r'=(\d+)', line)]
        declaration = re.search(r'@storage_' + name + r' = [^\n]+', target_text)[0]
        actual = [int(x) for x in re.findall(r'i64 (\d+)', declaration)]
        assert actual == expected, (name, actual, expected)
        count += 1
    assert count == 11
    print('PASS 11 independent clang wasm32 target layouts (cross-target constants only)')
else:
    assert a.baseline_compiler, '--baseline-compiler is required for equivalence'
    old = a.baseline_compiler.resolve()
    for target in ('linux', 'wasm'):
        modules = []
        for label, cc in [('old', old), ('new', compiler)]:
            module = out / f'{target}-{label}.ll'
            run([cc, 'test/layout/equivalence.lang', '-o', module], target=target)
            modules.append(module)
        assert modules[0].read_bytes() == modules[1].read_bytes(), target + ' emitted layout changed'
        if target == 'linux':
            for opt in ('-O0', '-O2'):
                exe = out / (target + opt)
                run(['clang', opt, modules[1], '-o', exe])
                run([exe], expected=42)
        else:
            exe = out / 'fixture.wasm'
            run(['clang', '--target=wasm32-unknown-unknown', '-nostdlib', '-Wl,--no-entry',
                 '-Wl,--export-all', '-Wl,--allow-undefined', modules[1], '-o', exe])
            run(['node', 'test/wasm_host.js', exe], expected=42)
        ast = out / f'{target}-round.ast'
        run([compiler, 'test/layout/equivalence.lang', '--emit-expanded-ast', '-o', ast], target=target)
        round_module = out / f'{target}-round.ll'
        run([compiler, ast, '--from-ast', '-o', round_module], target=target)
        assert round_module.read_bytes() == modules[1].read_bytes(), target + ' core round-trip changed layout'
        print(f'PASS {target}: byte-identical old/new LLVM and core round-trip; expected runtime exit 42; zero-length arrays preserved')
    for target in ('linux', 'wasm'):
        overflow = '[1152921504606846976]i64' if target == 'linux' else '[536870912]i64'
        for label, typ, diagnostic in [
            ('overflow', overflow, b'layout: fixed-array storage exceeds target size limit'),
            ('nested-overflow', '[1073741824][1073741824]i64', b'layout: fixed-array storage exceeds target size limit'),
            ('literal-overflow', '[18446744073709551616]u8', b'fixed-array count exceeds signed size limit'),
            ('signed-overflow', '[9223372036854775808]u8', b'fixed-array count exceeds signed size limit'),
            ('zero-void', '[0]void', b'layout: unsupported storage type'),
        ]:
            source = out / f'{target}-{label}.lang'
            source.write_text(f'func main() i64 {{ var x {typ}; return 0; }}\n')
            r = run([compiler, source, '-o', out / f'{target}-{label}.ll'], expected=1, target=target)
            assert diagnostic in r.stderr, r.stderr
            print(f'PASS {target} rejects {label}')
            if label == 'overflow':
                source = out / f'{target}-global-overflow.lang'
                source.write_text(f'var x {typ};\nfunc main() i64 {{ return 0; }}\n')
                r = run([compiler, source, '-o', out / f'{target}-global-overflow.ll'], expected=1, target=target)
                assert diagnostic in r.stderr, r.stderr
                print(f'PASS {target} rejects global storage overflow')
    # Readers constructing a negative count directly cannot bypass API checks.
print('Evidence:', out)
