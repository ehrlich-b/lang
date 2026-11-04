#!/usr/bin/env python3
"""Exercise the shared AST review formatter against stable interchange fixtures."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'test/fixtures/ast_format'
FORMATTER = ROOT / 'test/format_ast_e2e.js'
EXPECTED_COUNTS = {'effects': 26, 'empty': 1, 'escaped': 9, 'metadata': 11}
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
    return subprocess.run(['node', str(FORMATTER), str(path)], capture_output=True)


with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory) / 'formatted.ast'
    for source in sorted(FIXTURES.glob('*.input.ast')):
        golden = source.with_name(source.name.replace('.input.ast', '.golden.ast')).read_bytes()
        original = parse(source.read_text())
        first = format_file(source)
        assert first.returncode == 0, first.stderr
        assert first.stdout == golden, source
        temp.write_bytes(first.stdout)
        second = format_file(temp)
        assert second.returncode == 0, second.stderr
        assert second.stdout == first.stdout, source
        parsed = parse(second.stdout.decode())
        assert parsed == original and count(parsed) == count(original), source
        assert count(parsed) == EXPECTED_COUNTS[source.name.split('.')[0]], source
        assert str(ROOT).encode() not in first.stdout and str(temp).encode() not in first.stdout
        print(f'{source.name}: {count(parsed)} lists, golden and round trip OK')
    for bad in ['(program (func', '(program)) (program)', '(program (string "unterminated))', '(program /* unterminated']:
        temp.write_text(bad)
        result = format_file(temp)
        assert result.returncode != 0 and result.stderr and not result.stdout, bad
        print(f'rejected malformed: {bad}')
print('AST format contract passed')
