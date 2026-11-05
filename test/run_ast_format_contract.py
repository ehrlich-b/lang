#!/usr/bin/env python3
"""Exercise the shared AST review formatter against stable interchange fixtures."""
from pathlib import Path
import json
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test/fixtures/ast_format'
FORMATTER = ROOT / 'test/format_ast_e2e.js'
COMPILER = Path(os.environ.get('COMPILER', ROOT / 'out/lang_next')).resolve()
IDENTITY = FIXTURES / 'identity.lang'
assert COMPILER.is_file(), 'Build the native compiler first with make build'
# A table mismatch is a contract failure even before the shared cases run.
native_schema = dict(re.findall(r'if streq\(head, "([^"]+)"\) \{ return "([^"]*)";',
                                (ROOT / 'src/ast_shape.lang').read_text()))
browser_schema = dict(re.findall(r"^  '([^']+)': '([^']*)',", (ROOT / 'web/program_host.js').read_text(), re.M))
assert native_schema == browser_schema and native_schema, 'native/browser shape schemas differ'
EXPECTED_COUNTS = {'effects': 26, 'empty': 1, 'escaped': 9, 'metadata': 11, 'shapes': 24}
TOKEN = re.compile(r'''\s+|/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[()]|[^\s()]+''', re.S)


def parse(text):
    tokens = [m.group() for m in TOKEN.finditer(text)
              if not m.group().isspace() and not m.group().startswith(('/*', '//'))]
    def node(pos):
        if tokens[pos] != '(':
            assert tokens[pos] != ')'
            return tokens[pos], pos + 1
        result = []
        pos += 1
        while tokens[pos] != ')':
            child, pos = node(pos)
            result.append(child)
        return result, pos + 1
    tree, end = node(0)
    assert end == len(tokens)
    return tree


def count(tree):
    return 1 + sum(map(count, tree)) if isinstance(tree, list) else 0


def format_file(path):
    return subprocess.run(['node', str(FORMATTER), str(path)], capture_output=True, timeout=30)


def native_format(path, cache, compact=False):
    command = [str(COMPILER), 'read', str(IDENTITY), str(path)]
    if compact:
        command.append('--compact')
    return subprocess.run(command, capture_output=True, timeout=30,
                          env=dict(os.environ, LANGBE='llvm', LANG_CACHE=str(cache)))


with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory) / 'formatted.ast'
    cache = Path(directory) / 'cache'
    for source in sorted(FIXTURES.glob('*.input.ast')):
        golden = source.with_name(source.name.replace('.input.ast', '.golden.ast')).read_bytes()
        original = parse(source.read_text())
        native = native_format(source, cache)
        assert native.returncode == 0 and native.stdout == golden, (source, native)
        compact = native_format(source, cache, compact=True)
        assert compact.returncode == 0 and compact.stdout == source.read_bytes(), (source, compact)
        first = format_file(source)
        assert first.returncode == 0, first.stderr
        assert first.stdout == golden, source
        temp.write_bytes(first.stdout)
        second = format_file(temp)
        assert second.returncode == 0, second.stderr
        assert second.stdout == first.stdout, source
        native_second = native_format(temp, cache)
        assert native_second.returncode == 0 and native_second.stdout == second.stdout, native_second
        parsed = parse(second.stdout.decode())
        assert parsed == original and count(parsed) == count(original), source
        assert count(parsed) == EXPECTED_COUNTS[source.name.split('.')[0]], source
        assert str(ROOT).encode() not in first.stdout and str(temp).encode() not in first.stdout
        print(f'{source.name}: {count(parsed)} lists, native/browser golden, compact and round trip OK')
    for bad in ['(program (func', '(program)) (program)', '(program (string "unterminated))', '(program /* unterminated']:
        temp.write_text(bad)
        result = format_file(temp)
        assert result.returncode != 0 and result.stderr and not result.stdout, bad
        native = native_format(temp, cache)
        assert native.returncode == 1 and native.stderr and not native.stdout, (bad, native)
        print(f'native/browser rejected malformed: {bad}')
    # Balanced but structurally invalid input used to produce partial programs.
    # Prefix with multibyte trivia to assert byte locations, not JS code units.
    bad_nodes = [
        '(func)', '(func main (param x nil) nil nil)',
        '(func main ((param x)) nil nil)', '(func main () (type_ptr) nil)',
        '(func main () (type_base i64 extra) nil)',
        '(func main () nil (block (return (binop + (number 1)))))',
        '(func main () nil (block (return (number 1 extra))))',
        '(func main () nil (block (expr_stmt nil)))',
        '(func main () nil (block (return (mystery))))',
        '(func main () nil (block (return (bool maybe))))',
        '(func main () nil (block (return (span x 2 (number 1)))))',
        '(struct S ((param x nil)))', '(enum E ((variant_decl)))',
        '(effect Ask (oops) nil)', '(var x (type_base))',
        '(reader ast text)', '(macro m () (block) extra)',
        '(number 1)', 'nil', '(ast-version)',
    ]
    for rejected in bad_nodes:
        bad = '/* ☃ */ (program ' + rejected + ')'
        temp.write_text(bad)
        result = format_file(temp)
        assert result.returncode != 0 and not result.stdout, (bad, result)
        match = re.search(rb'ast-shape at bytes (\d+):(\d+)', result.stderr)
        assert match, (bad, result.stderr)
        span = tuple(map(int, match.groups()))
        assert 0 <= span[0] < span[1] <= len(bad.encode()), (bad, span)
        for compact in [False, True]:
            native = native_format(temp, cache, compact)
            assert native.returncode == 1 and not native.stdout, (bad, native)
            assert re.search(rb'ast-shape at bytes (\d+):(\d+)', native.stderr).groups() == match.groups(), native
        native = subprocess.run([str(COMPILER), '--diagnostics=json', str(IDENTITY), str(temp),
                                 '-o', str(Path(directory) / 'rejected.ll')],
                                capture_output=True, timeout=30)
        assert native.returncode == 1 and not native.stdout, (bad, native)
        records = [json.loads(line) for line in native.stderr.splitlines()]
        assert len(records) == 1 and records[0]['code'] == 'ast-shape', (bad, records)
        assert records[0]['path'] == str(temp), records
        assert records[0]['span'] is None, (bad, records)
        assert f'ast-shape at bytes {span[0]}:{span[1]}' in records[0]['message'], records
        if rejected == '(func)':
            assert bad.encode()[span[0]:span[1]] == b'(func)', span
        print(f'native/browser rejected shape at bytes {span[0]}:{span[1]}: {rejected}')
    inline = Path(directory) / 'inline.lang'
    inline.write_text('reader broken(text *u8) *u8 { return "(func)"; }\n'
                      'func main() i64 { return #broken{guest}; }\n')
    result = subprocess.run([str(COMPILER), '--diagnostics=json', str(inline),
                             '-o', str(Path(directory) / 'inline.ll')],
                            capture_output=True, timeout=30,
                            env=dict(os.environ, LANGBE='llvm', LANG_CACHE=str(cache)))
    assert result.returncode == 1 and not result.stdout, result
    records = [json.loads(line) for line in result.stderr.splitlines()]
    assert len(records) == 1 and records[0]['code'] == 'ast-shape', records
    assert records[0]['span'] is None, records
    assert 'ast-shape at bytes 0:6' in records[0]['message'], records
    print('inline reader rejects invalid expression; AST byte range and unmapped guest span stay separate')
print('AST format contract passed')
