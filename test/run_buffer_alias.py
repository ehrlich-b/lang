#!/usr/bin/env python3
"""Exercise buffer aliases and rejection on native and LLVM-to-Wasm."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
compiler = Path(os.environ.get('COMPILER', 'out/lang_next')).resolve()

def run(args, env, expected=0):
    p = subprocess.run([str(a) for a in args], env=env, capture_output=True, timeout=60)
    if p.returncode != expected:
        raise AssertionError((args, p.returncode, p.stdout, p.stderr))
    return p

# Expectations are built independently, preserving Python's slice snapshots.
b = bytearray(b'abcdef'); b.extend(b[:]); expected = bytes(b)
b.extend(b[2:9]); expected += bytes(b)
b.extend(b[3:3]); expected += bytes(b)
c = bytearray(b'x' * 255); c.extend(c[:]); c.extend(c[3:503]); c.extend(c[:]); expected += bytes(c)
d = bytearray(b'abcdef'); source = d[1:6]; d[3:8] = source; expected += bytes(d)
assert len(expected) == 2078
assert expected != expected[:-1]  # Negative control for the byte comparator.

with tempfile.TemporaryDirectory(prefix='buffer-alias-') as tmp:
    tmp = Path(tmp)
    for target in ('linux', 'wasm'):
        env = dict(os.environ, LANGBE='llvm', LANGOS=target, LANG_CACHE=str(tmp / 'cache'))
        def build(name, buffer_source, fixture):
            ir = tmp / (name + target + '.ll'); binary = tmp / (name + target)
            run([compiler, buffer_source, fixture, '-o', ir], env)
            link = ['clang', '-O0']
            if target == 'wasm':
                link += ['--target=wasm32-unknown-unknown', '-nostdlib', '-Wl,--no-entry', '-Wl,--export-all', '-Wl,--allow-undefined']
            run(link + [ir, '-o', binary], env)
            return [binary] if target == 'linux' else ['node', 'test/wasm_host.js', binary]
        p = run(build('alias', 'std/core.lang', 'test/buffer_alias/alias.lang'), env)
        assert p.stdout == expected, (target, len(p.stdout), len(expected))
        print(target, 'whole, interior, empty, capacity and repeated growth: bytes match', len(expected))
        # Instrument only the error sink to observe state after rejection; the
        # append and reserve implementation remains the production source.
        source = Path('std/buffer.lang').read_text()
        marker = '    exit(1);\n}'
        assert source.count(marker) == 1
        source = source.replace(marker, '''    if watched == nil || watched.data != saved_data || watched.len != 3 || watched.cap != saved_cap { exit(9); }
    file_write(1, watched.data, watched.len + 1);
    exit(1);
}''')
        assert source.count('var data *u8 = alloc(cap);') == 1
        source = source.replace('var data *u8 = alloc(cap);', 'var data *u8 = checked_alloc(cap);')
        instrumented = tmp / 'buffer.lang'; instrumented.write_text(source)
        core = tmp / 'core.lang'
        core.write_text(Path('std/core.lang').read_text().replace('include "std/buffer.lang"', 'include "' + str(instrumented) + '"'))
        template = Path('test/buffer_alias/reject.lang').read_text()
        for name, action, error in [
            ('negative', 'phase_buffer_append(watched, watched.data, 0 - 1);', b'byte-limit'),
            ('limit', 'phase_buffer_append(watched, watched.data, 4);', b'byte-limit'),
            ('allocation', 'watched.cap = 4; saved_cap = 4; fail_alloc = 1; phase_buffer_append(watched, watched.data, 3);', b'allocation-failed'),
        ]:
            fixture = tmp / (name + '.lang'); fixture.write_text(template.replace('REJECT_ACTION', action))
            p = run(build(name, core, fixture), env, expected=1)
            assert p.stdout == b'abc\0' and error in p.stderr, (target, name, p.stdout, p.stderr)
            print(target, name, 'rejected; pointer, length, capacity, bytes and sentinel unchanged')
print('PASS buffer alias and rejection checks')
