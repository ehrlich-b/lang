#!/usr/bin/env python3
"""Check source byte spans and the LF-only, 1-based byte-column contract."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
fixture = Path('test/tok_crlf.fixture').read_bytes()
# Tokens are specified by source bytes, independently of tokenizer offsets.
cases = [
    ('mixed', fixture, [(2, b'alpha'), (3, '"café 🧭"'.encode()), (2, b'beta'), (1, b'42'), (99, '🧭'.encode())]),
    ('crlf', b'a\r\n\tb', [(2, b'a'), (2, b'b')]),
    ('lone-cr', b'a\r\tb', [(2, b'a'), (2, b'b')]),
    ('string', '"é🧭\r\n\tend" z'.encode(), [(3, '"é🧭\r\n\tend"'.encode()), (2, b'z')]),
    ('error', 'ok\r\n\t/* é🧭\rbroken'.encode(), [(2, b'ok'), (99, '/* é🧭\rbroken'.encode())]),
    ('empty', b'', []),
]

def expected(source, tokens):
    cursor = 0
    rows = []
    for kind, raw in tokens + ([] if tokens and tokens[-1][1].startswith(b'/*') else [(0, b'')]):
        start = source.index(raw, cursor) if raw else len(source)
        end = start + len(raw)
        prefix = source[:start]
        line = prefix.count(b'\n') + 1
        column = len(prefix.rsplit(b'\n', 1)[-1]) + 1
        rows.append((kind, start, end, line, column, raw))
        cursor = end
    return rows

def check(actual, want):
    assert actual == want, (actual, want)

with tempfile.TemporaryDirectory(prefix='tok-crlf-') as tmp:
    exe = Path(tmp) / 'probe'
    subprocess.run([os.environ.get('COMPILER', './out/lang_next'), 'test/tok_crlf_probe.lang', '-o', str(exe) + '.ll'], check=True, stdout=subprocess.PIPE)
    subprocess.run(['clang', str(exe) + '.ll', '-o', str(exe)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for name, source, tokens in cases:
        path = Path(tmp) / 'input'
        path.write_bytes(source)
        output = subprocess.check_output([str(exe), str(path)])
        rows = []
        while output:
            header, output = output.split(b'\n', 1)
            kind, start, end, line, column = map(int, header.split())
            raw, output = output[:end-start], output[end-start:]
            assert output[:1] == b'\n'
            output = output[1:]
            rows.append((kind, start, end, line, column, raw))
        want = expected(source, tokens)
        check(rows, want)
        if name == 'mixed':
            wrong = list(want)
            row = wrong[1]
            wrong[1] = row[:4] + (row[4] + 1,) + row[5:]
            try:
                check(rows, wrong)
            except AssertionError:
                print('PASS negative control: wrong byte column rejected')
            else:
                raise AssertionError('wrong column accepted')
        print('PASS', name, len(rows), 'tokens with original bytes')
