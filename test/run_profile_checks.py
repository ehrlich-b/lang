#!/usr/bin/env python3
"""Executable boundaries for the published profiles; retain every artifact."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    os.chdir(ROOT)
    output = (args.output or Path(tempfile.mkdtemp(prefix='profiles-', dir=ROOT / 'out'))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    compiler = str(Path(os.environ.get('COMPILER', './out/lang')).resolve())
    env = dict(os.environ, LANGBE='llvm', LANGOS='macos' if os.uname().sysname == 'Darwin' else 'linux',
               LANG_CACHE=str(output / 'cache'))
    rows = []

    def check(name, command, *, diagnostic=None, data=None, success=True, run_env=env, empty_stdout=False):
        result = subprocess.run(command, input=data, capture_output=True, env=run_env, timeout=180)
        (output / f'{name}.stdout').write_bytes(result.stdout)
        (output / f'{name}.stderr').write_bytes(result.stderr)
        (output / f'{name}.exit').write_text(f'{result.returncode}\n')
        good = result.returncode == 0 if success else result.returncode > 0
        if empty_stdout:
            good &= not result.stdout
        if diagnostic:
            good &= diagnostic.encode() in result.stderr
        rows.append({'name': name, 'command': list(map(str, command)), 'exit': result.returncode, 'pass': bool(good)})
        print(f'{"PASS" if good else "FAIL"} {name}', flush=True)
        if not good:
            print(result.stderr.decode(errors='replace')[-3000:], flush=True)
        return result

    def source(name, text):
        path = output / name
        path.write_text(text)
        return str(path)

    probe = str(output / 'probe')
    ir = str(output / 'probe.ll')
    check('probe-emit', [compiler, 'test/profile_limits_probe.lang', '-o', ir])
    check('probe-link', [os.environ.get('CLANG', 'clang'), '-O0', ir, '-o', probe])
    for mode in ('ast', 'render', 'wrapper'):
        check(mode + '-boundary', [probe, mode])
    for mode, diagnostic in [('ast-over', 'AST output'), ('render-over', 'AST source output'),
                             ('assembly', 'assembly output'), ('write', 'cannot write compiler output'),
                             ('llvm-output', 'LLVM output buffer overflow'), ('wasm-output', 'wasm output buffer overflow'),
                             ('wrapper-over', 'reader wrapper')]:
        check(mode, [probe, mode], diagnostic=diagnostic, success=False)
    check('read-boundary', [probe, 'read'], data=b'x' * 15)
    check('read-over', [probe, 'read'], data=b'x' * 16, diagnostic='probe input', success=False)
    # A separate executable deliberately sends a valid prefix and excess bytes.
    # No subprocess implementation replaces any target program semantics.
    for size in (15, 16, 65536):
        child = Path(source(f'writer-{size}', '#!/usr/bin/env python3\nimport sys\nsys.stdout.buffer.write(b"(program)" + b" " * (' + str(size) + ' - 9))\n'))
        child.chmod(0o755)
        check(f'capture-{size}', [probe, 'capture', str(child)], success=size == 15,
              diagnostic='reader stdout' if size > 15 else None)

    valid = 'func main() i64 { return 0; }\n'
    # Comments make large inputs cheap to parse; a valid prefix must not hide a tail.
    def padded(prefix, length):
        return prefix + '/*' + ' ' * (length - len(prefix) - 4) + '*/'
    mib = 1024 * 1024
    inc = source('include-boundary.lang', padded(valid, mib - 1))
    check('include-boundary', [compiler, inc, '-o', str(output / 'include.ll')])
    over = source('include-over.lang', padded(valid, mib))
    for mode, flags in [('include-over', []), ('expanded-over', ['--emit-expanded-ast'])]:
        check(mode, [compiler, over, *flags, '-o', str(output / (mode + '.out'))],
              diagnostic='size limit exceeded: ' + over, success=False)
    large = source('file-boundary.lang', padded(valid, 8 * mib - 1))
    check('file-boundary', [compiler, '--dump-tokens', large])
    large_over = source('file-over.lang', padded(valid, 8 * mib))
    check('file-over', [compiler, '--dump-tokens', large_over], diagnostic='size limit exceeded: ' + large_over, success=False)
    ast_text = '(program (func main () (type_base i64) (block (return (number 0)))))'
    ast = source('ast-boundary.ast', ast_text + ' ' * (8 * mib - 1 - len(ast_text.encode())))
    check('ast-input-boundary', [compiler, '--from-ast', ast, '-o', str(output / 'ast.ll')])
    ast_over = source('ast-over.ast', ast_text + ' ' * (8 * mib - len(ast_text.encode())))
    check('ast-input-over', [compiler, '--from-ast', ast_over, '-o', str(output / 'ast-over.ll')],
          diagnostic='size limit exceeded: ' + ast_over, success=False)

    # Real generated reader stdin: the source is below the CLI file limit.
    reader = source('bounded.lang', 'reader bounded(text *u8) *u8 { return "(program)"; }\n')
    custom = source('input.bounded', ' ' * (4 * mib - 1))
    check('reader-stdin-boundary', [compiler, 'read', reader, custom, '--compact'])
    custom_over = source('over.bounded', ' ' * (4 * mib))
    check('reader-stdin-over', [compiler, 'read', reader, custom_over, '--compact'],
          diagnostic='size limit exceeded: reader stdin', success=False, empty_stdout=True)
    check('combined-source-over', [compiler, reader, custom_over, '-o', str(output / 'combined.ll')],
          diagnostic='size limit exceeded: combined source', success=False)

    noisy = source('noisy.lang', 'include "std/core.lang"\nreader noisy(text *u8) *u8 { var s *u8 = alloc(4194305); memcpy(s, "(program)", 9); var i i64 = 9; while i < 4194304 { *(s + i) = 32; i = i + 1; } *(s + i) = 0; return s; }\n')
    tiny = source('input.noisy', 'x')
    check('reader-stdout-over', [compiler, 'read', noisy, tiny, '--compact'],
          diagnostic='size limit exceeded: reader stdout', success=False, empty_stdout=True)

    aggregate = source('struct-return.lang', 'struct Pair { a i64; b i64; }\nfunc pair() Pair { var p Pair; p.a = 20; p.b = 22; return p; }\nfunc main() i64 { pair(); return 0; }\n')
    for backend in ('llvm', 'x86', 'wasm'):
        if backend == 'x86' and os.uname().sysname != 'Linux':
            continue  # x86/Linux is a different published target, never claimed on Mac.
        diagnostic = 'scalar, pointer, or void returns' if backend == 'wasm' else 'struct value returns are unsupported'
        check('struct-return-' + backend, [compiler, aggregate, '-o', str(output / ('struct.' + backend))],
              diagnostic=diagnostic, success=False,
              run_env=dict(env, LANGBE=backend, LANGOS='wasm' if backend == 'wasm' else env['LANGOS']))
    # Preserve legacy C semantics explicitly: a non-breaking case does not fall through.
    c = source('legacy.c', 'int answer(int n) { switch(n) { case 1: n = 40; case 2: n = n + 2; } return n; }\n')
    host = source('legacy.lang', 'func main() i64 { if answer(1) != 40 { return 1; } if answer(2) != 4 { return 2; } return 0; }\n')
    legacy_ir = str(output / 'legacy.ll')
    check('legacy-c-emit', [compiler, 'example/c/c.lang', c, host, '-o', legacy_ir])
    check('legacy-c-link', [os.environ.get('CLANG', 'clang'), '-O2', legacy_ir, '-o', str(output / 'legacy')])
    check('legacy-c-run', [str(output / 'legacy')])
    emitted = Path(legacy_ir).read_text()
    good = 'define i64 @answer(i64' in emitted
    rows.append({'name': 'legacy-c-int-i64', 'pass': good})
    print(f'{"PASS" if good else "FAIL"} legacy-c-int-i64', flush=True)
    (output / 'receipt.json').write_text(json.dumps(rows, indent=2) + '\n')
    return 0 if all(row['pass'] for row in rows) else 1

if __name__ == '__main__':
    raise SystemExit(main())
