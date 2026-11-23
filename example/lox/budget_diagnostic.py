#!/usr/bin/env python3
"""Render a located error when the parser host stops before the reader can report."""
import json
from pathlib import Path
import sys
import unicodedata


def width(text):
    return sum(2 if unicodedata.east_asian_width(char) in 'FW' else 1 for char in text)


def main(path, log):
    source = Path(path).read_bytes()
    messages = {
        'parser-depth-budget': 'Lox syntax nesting exceeds the parser limit.',
        'parser-work-budget': 'Lox program exceeds the parser work limit.',
    }
    for record in Path(log).read_text().splitlines():
        diagnostic = json.loads(record)
        message = messages.get(diagnostic['code'])
        if message is None or diagnostic['path'] != path or not diagnostic['span']:
            continue
        start = diagnostic['span']['start']
        end = diagnostic['span']['end']
        if not 0 <= start <= end <= len(source):
            return 1
        line_start = source.rfind(b'\n', 0, start) + 1
        line_end = source.find(b'\n', start)
        if line_end < 0:
            line_end = len(source)
        line = source[line_start:line_end].removesuffix(b'\r')
        prefix = line[:start - line_start].decode()
        marker = ''.join('\t' if char == '\t' else ' ' * width(char) for char in prefix)
        column = width(marker.expandtabs(8))
        span = line[start - line_start:end - line_start].decode()
        carets = 0
        for char in span:
            carets += 8 - (column + carets) % 8 if char == '\t' else width(char)
        number = source.count(b'\n', 0, start) + 1
        print(f'{path}:{number}:{start - line_start + 1}: {message} @{start}:{end}', file=sys.stderr)
        print(line.decode(), file=sys.stderr)
        print(marker + '^' * max(1, carets), file=sys.stderr)
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
