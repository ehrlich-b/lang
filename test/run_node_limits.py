#!/usr/bin/env python3
"""Exercise the real structural boundary, then compile and run just below it."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
COMPILER = str((ROOT / os.environ.get('COMPILER', 'out/lang_next')).resolve())
DEFAULT = 4194304

def nodes(text):
    return len(re.findall(r'\(|[^\s()]+', text))


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix='node-limits-') as folder:
        work = Path(folder)
        env = {k: v for k, v in os.environ.items() if not k.startswith('LANG_HOST_MAX_')}
        env['LANGBE'] = 'llvm'

        def run(name, args, expected=0, settings=None, diagnostic=None, data=b''):
            start = time.perf_counter()
            proc = subprocess.run([str(a) for a in args], env=dict(env, **(settings or {})),
                                  input=data, capture_output=True, timeout=60, cwd=ROOT)
            assert proc.returncode == expected, (name, proc.returncode, proc.stderr[-2000:])
            if diagnostic:
                assert not proc.stdout and diagnostic.encode() in proc.stderr, (name, proc.stderr)
            results.append(dict(name=name, seconds=time.perf_counter() - start,
                                command=[str(a) for a in args], exit_code=proc.returncode,
                                stderr=proc.stderr.decode(errors='replace')))
            print('PASS', name, flush=True)
            return proc

        # Compact sibling blocks test the actual default without a 100k-line
        # fixture or millions of LLVM instructions. No node setting is supplied.
        prefix = '(program (func main () (type_base i64) (block '
        suffix = '(return (number 0)))))'
        base = nodes(prefix + suffix)
        count = (DEFAULT - 1 - base) // 2
        below = prefix + '(block)' * count + suffix
        actual = nodes(below)
        assert DEFAULT - 2 <= actual < DEFAULT
        path = work / 'under-default.ast'
        path.write_text(below)
        ir = work / 'under-default.ll'
        run('under-default-compile', [COMPILER, '--from-ast', path, '-o', ir])
        binary = work / 'under-default'
        run('under-default-link', ['clang', '-O2', ir, '-o', binary])
        run('under-default-native', [binary])
        over = work / 'over-default.ast'
        over.write_text(prefix + '(block)' * (count + 2) + suffix)
        refused = run('over-default', [COMPILER, '--from-ast', over, '-o', work / 'over.ll'],
                      expected=1, diagnostic='(code ast-nodes)')
        assert str(over).encode() in refused.stderr
        assert str(DEFAULT).encode() in refused.stderr and b'LANG_HOST_MAX_NODES' in refused.stderr
        assert not (work / 'over.ll').exists()

        # Exact configured boundary and one more element, using valid core AST.
        small = work / 'small.ast'
        small.write_text(prefix + suffix)
        run('exact-configured', [COMPILER, '--from-ast', small, '-o', work / 'exact.ll'],
            settings={'LANG_HOST_MAX_NODES': str(base)})
        refused = run('over-configured', [COMPILER, '--from-ast', small, '-o', work / 'refused.ll'],
                      expected=1, settings={'LANG_HOST_MAX_NODES': str(base - 1)}, diagnostic='ast-nodes')
        assert str(base - 1).encode() in refused.stderr and str(small).encode() in refused.stderr
        for index, value in enumerate(['0', '-1', 'x', '16777217', '999999999999999999999']):
            run('invalid-' + str(index), [COMPILER, '--from-ast', small, '-o', work / 'invalid.ll'],
                expected=1, settings={'LANG_HOST_MAX_NODES': value}, diagnostic='invalid-node-limit')
        run('maximum-configured', [COMPILER, '--from-ast', small, '-o', work / 'maximum.ll'],
            settings={'LANG_HOST_MAX_NODES': '16777216'})
        source = work / 'tokens.lang'
        source.write_text('func main() i64 { return 0; }')
        run('source-nodes', [COMPILER, source, '-o', work / 'tokens.ll'], expected=1,
            settings={'LANG_HOST_MAX_NODES': '8'}, diagnostic='source-nodes')
        probe_ir = work / 'probe.ll'
        probe = work / 'probe'
        run('probe-compile', [COMPILER, 'test/phase_host/probe.lang', '-o', probe_ir])
        run('probe-link', ['clang', '-O2', probe_ir, '-o', probe])
        for name, text in [('empty', ''), ('mixed', 'é\n\nabc\r\nz\n'), ('no-newline', 'hello é')]:
            run('span-index-' + name, [probe, 'span-index'], data=text.encode())
        run('emitted-nodes', [probe, 'emit-nodes'], expected=1,
            settings={'LANG_HOST_MAX_NODES': '2'}, diagnostic='ast-nodes')
        run('origin-nodes', [probe, 'span-index'], expected=1, data=b'abc',
            settings={'LANG_HOST_MAX_NODES': '2'}, diagnostic='origin-budget')
    report = os.environ.get('NODE_LIMIT_EVIDENCE')
    if report:
        Path(report).write_text(json.dumps(dict(default=DEFAULT, under_nodes=actual, checks=results), indent=2) + '\n')
    print('Structural boundary checks passed;', actual, 'nodes compiled at defaults')


if __name__ == '__main__':
    main()
