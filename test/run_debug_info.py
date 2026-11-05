#!/usr/bin/env python3
"""Check reader origins in native DWARF, verified IR, and unchanged non-debug IR.

Run from any directory. LLVM's opt, clang, and llvm-dwarfdump must be on PATH.
Use --base-ref REV to rebuild that revision and compare non-debug output too.
Artifacts and command receipts go to --output (outside the checkout).
"""
import argparse
import hashlib
import gzip
import difflib
import io
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def line_of(path, statement):
    lines = Path(path).read_text().splitlines()
    matches = [i for i, line in enumerate(lines, 1) if statement in line]
    assert len(matches) == 1, (path, statement, matches)
    return matches[0]


def line_rows(dump):
    """Resolve each row's file index within its own .debug_line table."""
    files, rows, index = {}, {}, None
    for line in dump.splitlines():
        if line.startswith('debug_line['):
            files, index = {}, None
        match = re.match(r'file_names\[\s*(\d+)\]:', line)
        if match:
            index = int(match[1])
        match = re.match(r'\s+name: "(.*)"', line)
        if match and index is not None:
            files[index] = match[1]
            index = None
        match = re.match(r'0x[0-9a-fA-F]+\s+(\d+)\s+(\d+)\s+(\d+)\s+', line)
        if match and 'end_sequence' not in line:
            lineno, column, file_id = map(int, match.groups())
            name = files.get(file_id)
            if name:
                rows.setdefault(name, set()).add((lineno, column))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', help='existing compiler; otherwise make build')
    parser.add_argument('--base-ref', help='git revision to rebuild for byte comparison')
    parser.add_argument('--base-compiler', help='existing base compiler for byte comparison')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    os.chdir(ROOT)
    output = (args.output or Path(tempfile.mkdtemp(prefix='debug-info-evidence-'))).resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('--output must be outside the checkout')
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, LANGBE='llvm', JOBS='2')
    receipts = []

    def run(command, label, cwd=ROOT, expected=0):
        result = subprocess.run(list(map(str, command)), cwd=cwd, env=env,
                                capture_output=True, timeout=600)
        prefix = output / label
        if label.endswith('-lines'):
            prefix.with_suffix('.stdout.gz').write_bytes(gzip.compress(result.stdout, mtime=0))
        else:
            prefix.with_suffix('.stdout').write_bytes(result.stdout)
        prefix.with_suffix('.stderr').write_bytes(result.stderr)
        receipts.append(dict(command=list(map(str, command)), cwd=str(cwd),
                             exit=result.returncode, label=label))
        (output / 'commands.json').write_text(json.dumps(receipts, indent=2) + '\n')
        if expected is not None and result.returncode != expected:
            raise AssertionError(f'{label}: exit {result.returncode}; {result.stderr.decode(errors="replace")}')
        return result

    with tempfile.TemporaryDirectory(prefix='lang-debug-info-') as temporary:
        work = Path(temporary)
        env['LANG_CACHE'] = str(work / 'cache')
        if args.compiler:
            compiler = Path(args.compiler).resolve()
        else:
            run(['make', 'build'], 'build')
            compiler = (ROOT / 'out/lang_next').resolve()
        base = Path(args.base_compiler).resolve() if args.base_compiler else None
        if args.base_ref:
            archive = run(['git', 'archive', args.base_ref], 'base-archive').stdout
            # Do not retain the binary archive in the command log.
            (output / 'base-archive.stdout').write_text(hashlib.sha256(archive).hexdigest() + '\n')
            snapshot = work / 'base'
            snapshot.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archive)) as source:
                source.extractall(snapshot, filter='data')
            # Build archived source with its preserved seed, without requiring
            # Git metadata or making a second checkout's build receipt.
            platform = 'macos' if sys.platform == 'darwin' else 'linux'
            seed = work / 'base-seed'
            run(['clang', '-O2', snapshot / f'bootstrap/current/compiler_{platform}.ll',
                 '-o', seed], 'base-seed')
            (snapshot / 'std/os.lang').write_text(
                'include "std/os/libc_macos.lang"\n' if platform == 'macos'
                else 'include "std/os/libc.lang"\n')
            version = snapshot / 'version_info.lang'
            version.write_bytes((ROOT / 'out/version_info.lang').read_bytes())
            sources = ['std/core.lang', 'version_info.lang', 'src/lexer.lang',
                       'src/parser.lang', 'src/codegen.lang', 'src/codegen_llvm.lang',
                       'src/codegen_wasm.lang', 'src/ast_emit.lang', 'src/sexpr_reader.lang',
                       'src/compiler_readers_none.lang', 'src/main.lang']
            baseline_ir = work / 'base-compiler.ll'
            run([seed, *sources, '-o', baseline_ir], 'base-build', cwd=snapshot)
            base = work / 'base-compiler'
            run(['clang', '-O2', baseline_ir, '-o', base], 'base-link')
        cases = [
            ('lang', ['test/debug_info/native.lang'],
             {'test/debug_info/native.lang': ['return n * 2;', 'var value i64 = twice(21);',
                                               'println("debug native");', 'return value - 42;']}),
            ('native-lambda', ['test/debug_info/lambda.lang'],
             {'test/debug_info/lambda.lang': ['return n * 3;', 'return value + offset;',
                                               'return inner(10);', 'return outer() - 22;']}),
            ('minilisp', ['std/core.lang', 'example/minilisp/lisp_runtime.lang',
                          'example/minilisp/minilisp.lang', 'test/debug_info/program.minilisp',
                          'test/debug_info/lisp_host.lang'],
             {'test/debug_info/program.minilisp': ['(+ x 2)']}),
            ('forth', ['std/core.lang', 'example/forth/forth_runtime.lang',
                       'example/forth/forth.lang', 'test/debug_info/program.forth'],
             {'test/debug_info/program.forth': [': debug_forth', '40 debug_forth']}),
            ('minipy', ['std/core.lang', 'example/minipy/minipy_runtime.lang',
                        'example/minipy/minipy.lang', 'test/debug_info/program.minipy'],
             {'test/debug_info/program.minipy': ['return n + 2', 'value = debug_py(40)',
                                                 'return value - 42']}),
            ('polyglot', ['example/polyglot.lang'],
             {'example/polyglot.lang': [': divides?', 'if (divides_p(d, x))',
                                        '(defun ml_sum', 'yield x;', 'lst = collect_primes(n)',
                                        'var best i64 = survey(30);']}),
            # One binary must retain distinct source-file indexes for every
            # reader; it must not report the generated reader wrappers instead.
            ('mixed', ['std/core.lang', 'example/minilisp/lisp_runtime.lang',
                       'example/minilisp/minilisp.lang', 'example/forth/forth_runtime.lang',
                       'example/forth/forth.lang', 'example/minipy/minipy_runtime.lang',
                       'example/minipy/minipy.lang', 'test/debug_info/program.minilisp',
                       'test/debug_info/program.forth', 'test/debug_info/helpers.minipy'],
             {'test/debug_info/program.minilisp': ['(+ x 2)'],
              'test/debug_info/program.forth': ['40 debug_forth'],
              'test/debug_info/helpers.minipy': ['return debug_py(n)'],
              'example/minipy/minipy_runtime.lang': ['func py_space()']}),
        ]
        summary = []
        for name, inputs, expected_files in cases:
            ir = work / f'{name}.ll'
            run([compiler, '-g', *inputs, '-o', ir], f'{name}-emit')
            text = ir.read_text()
            for required in ('!DICompileUnit(', '!DISubprogram(', '!DILocation('):
                assert required in text, (name, required)
            if name == 'native-lambda':
                # Deferred functions need their own scopes, including lambdas
                # discovered while emitting another lambda's body.
                for index, statement in enumerate(('return n * 3;', 'return inner(10);',
                                                   'return value + offset;')):
                    symbol = f'__lambda_{index}'
                    function = re.search(rf'^define [^\n]*@{symbol}\([^\n]* !dbg !(\d+) \{{\n(.*?)^}}',
                                         text, re.M | re.S)
                    assert function, (symbol, 'missing subprogram attachment')
                    scope, body = function.groups()
                    assert re.search(rf'^!{scope} = distinct !DISubprogram\(name: "{symbol}"',
                                     text, re.M), (symbol, scope)
                    location = re.search(r'ret i64 [^\n]*, !dbg !(\d+)', body)
                    assert location, (symbol, 'missing return location')
                    line = line_of('test/debug_info/lambda.lang', statement)
                    assert re.search(rf'^!{location[1]} = !DILocation\(line: {line}, column: \d+, scope: !{scope}\)',
                                     text, re.M), (symbol, line, location[1])
            run(['opt', '-passes=verify', '-disable-output', ir], f'{name}-verify')
            checked = {}
            for level in ('O0', 'O2'):
                binary = work / f'{name}-{level}'
                run(['clang', f'-{level}', ir, '-o', binary], f'{name}-{level}-link')
                run([binary], f'{name}-{level}-run')
                run(['llvm-dwarfdump', '--verify', binary], f'{name}-{level}-dwarf-verify')
                dump = run(['llvm-dwarfdump', '--debug-line', binary], f'{name}-{level}-lines').stdout.decode()
                rows = line_rows(dump)
                expected_rows = {}
                for path, statements in expected_files.items():
                    basename = Path(path).name
                    actual = {line for file, entries in rows.items() if Path(file).name == basename
                              for line, column in entries}
                    expected = {line_of(path, statement) for statement in statements}
                    # Optimization may fold a statement away. Polyglot's
                    # effects keep its debug functions unoptimized at O2.
                    assert actual, (name, level, path, rows)
                    if level == 'O0' or name == 'polyglot':
                        assert expected <= actual, (name, path, expected, actual)
                    expected_rows[path] = dict(expected=sorted(expected), actual=sorted(actual))
                checked[level] = expected_rows
            plain = work / f'{name}-plain.ll'
            run([compiler, *inputs, '-o', plain], f'{name}-plain')
            assert b'!dbg' not in plain.read_bytes()
            if base:
                baseline = work / f'{name}-base.ll'
                run([base, *inputs, '-o', baseline], f'{name}-base')
                if baseline.read_bytes() != plain.read_bytes():
                    (output / f'{name}-plain.diff').write_text(''.join(difflib.unified_diff(
                        baseline.read_text().splitlines(True), plain.read_text().splitlines(True),
                        fromfile='base', tofile='candidate')))
                    raise AssertionError(f'{name}: non-debug IR changed')
            summary.append(dict(case=name, debug_ir_sha256=hashlib.sha256(ir.read_bytes()).hexdigest(),
                                plain_ir_sha256=hashlib.sha256(plain.read_bytes()).hexdigest(),
                                base_identical=bool(base), lines=checked))
            print(f'PASS {name}: verified DWARF/IR, native execution, line rows, non-debug output')
        # Exercise the minted-compiler entry point as well as the full CLI.
        minted = work / 'tinyc'
        run([compiler, 'compiler', 'tiny', 'example/tiny/tiny.lang', '-o', minted], 'mint-tiny')
        minted_ir = work / 'tiny.ll'
        run([minted, '-g', 'example/tiny/answer.tiny', '-o', minted_ir], 'mint-tiny-debug')
        run(['opt', '-passes=verify', '-disable-output', minted_ir], 'mint-tiny-verify')
        assert '!DISubprogram(' in minted_ir.read_text()
        # Unlocated saved AST must never borrow a previous function's location.
        unlocated = work / 'unlocated.ast'
        unlocated.write_text('(program (func main () (type_base i64) (block (return (number 0)))))')
        unlocated_ir = work / 'unlocated.ll'
        run([compiler, '-g', '--from-ast', unlocated, '-o', unlocated_ir], 'unlocated-emit')
        run(['opt', '-passes=verify', '-disable-output', unlocated_ir], 'unlocated-verify')
        assert '!DILocation(' not in unlocated_ir.read_text()
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f'Debug info: PASS ({len(cases)} cases); evidence: {output}')


if __name__ == '__main__':
    main()
