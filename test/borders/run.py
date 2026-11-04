#!/usr/bin/env python3
"""Execute the same small feature probes against both backends."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
compiler = str(ROOT / 'out/lang_next')
readers = ('lang', 'minipy', 'minilisp')
features = ('integers', 'floats', 'strings', 'functions', 'structs')

def run(args, env=None):
    try:
        p = subprocess.run(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        return p.returncode, p.stdout.decode(errors='replace')[-2000:]
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f'probe timed out: {args}') from exc

with tempfile.TemporaryDirectory(prefix='borders-zig-') as zig_cache:
    zig_code, zig_detail = run([compiler, 'read', 'example/c/c.lang', 'test/borders/missing.zig'],
                               dict(os.environ, LANG_CACHE=zig_cache))
if zig_code == 0 or 'test/borders/missing.zig:1:1: error:' not in zig_detail or "reader 'zig' not found" not in zig_detail:
    raise SystemExit('Zig missing-reader check failed: ' + zig_detail)

cells = []
with tempfile.TemporaryDirectory(prefix='borders-') as temp:
    for reader in readers:
        for feature in features:
            for target in ('llvm', 'wasm'):
                fixture = f'test/borders/cases/{reader}_{feature}.lang'
                output = Path(temp) / ('program.ll' if target == 'llvm' else 'program.wasm')
                env = dict(os.environ, LANGBE=target, LANGOS='linux' if target == 'llvm' else 'wasm', LANG_CACHE=str(Path(temp) / 'cache'))
                code, detail = run([compiler, fixture, '-o', str(output)], env)
                if code:
                    status = 'crash' if code < 0 else 'rejected'
                else:
                    if target == 'llvm':
                        binary = str(Path(temp) / 'program')
                        code, detail = run(['clang', str(output), '-o', binary])
                        command = [binary]
                    else:
                        command = ['node', 'test/wasm_host.js', str(output)]
                    if not code:
                        code, detail = run(command, dict(os.environ, LANG_BORDERS_TRAPS='1'))
                        status = 'supported' if code == 42 else ('crash' if code < 0 or (target == 'wasm' and code == 139 and 'borders: wasm trap' in detail) else 'wrong')
                    else:
                        status = 'crash' if code < 0 else 'rejected'
                if status in ('wrong', 'crash'):
                    bug = f'test/borders/bugs/{reader}_{feature}_{target}.lang'
                    shutil.copyfile(fixture, bug)
                    fixture = bug
                cells.append(dict(reader=reader, feature=feature, target=target, status=status, fixture=fixture, exit_code=code, detail=detail))
Path('borders.json').write_text(json.dumps({'cells': cells}, indent=2) + '\n')
lines = ['# Borders', '', 'Zig has no current reader or AIR importer.', 'The previous experimental approaches were removed.', 'A maintained frontend for a defined subset is needed.', '', 'See [Zig status](../ZIG-STATUS.md) for the history.', '', '| Reader | Feature | LLVM x86-64 | Wasm |', '| --- | --- | --- | --- |']
for reader in readers:
    for feature in features:
        pair = [c for c in cells if c['reader'] == reader and c['feature'] == feature]
        links = [f"[{c['status']}](../{c['fixture']})" for c in pair]
        lines.append(f'| {reader} | {feature} | {links[0]} | {links[1]} |')
lines += ['| Zig | missing reader | [rejected at line 1](../test/borders/missing.zig#L1) | [rejected at line 1](../test/borders/missing.zig#L1) |', '', 'Zig is rejected before target selection.', '', 'Each result is from compiling and running its fixture; a rejection is a compiler or linker error. Exit 42 is the expected result. See `borders.json` for diagnostics and exit codes.']
Path('docs/BORDERS.md').write_text('\n'.join(lines) + '\n')
print('Wrote borders.json and docs/BORDERS.md')
