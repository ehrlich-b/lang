#!/usr/bin/env python3
"""Read suite headers once; emit NUL-delimited worker arguments.

Explicit paths select a fragment; with no paths the complete suite is selected.
Expected values remain strings: unknown headers must not become passing zeros.
"""
import argparse
import glob
import os
import re
import sys


def classify(path):
    with open(path, 'rb') as source:
        lines = [source.readline() for _ in range(3)]
    first = lines[0]
    header = b''.join(lines)
    markers = ''.join(flag for flag, present in (
        ('i', b'//ignore' in first),
        ('l', b'//linux' in header),
        ('m', b'//macos' in header),
        ('r', first.startswith(b'// reject: ')),
        ('c', b'//clang' in header),
    ) if present).encode()
    # Match grep -o '[0-9]*' and shell command substitution exactly, including
    # multiple matches, leading zeros, and rejection messages containing digits.
    expected = b'\n'.join(re.findall(rb'[0-9]+', first))
    diagnostic = first[len(b'// reject: '):].rstrip(b'\n') if b'r' in markers else b''
    return os.fsencode(path), markers, expected, diagnostic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata-only', action='store_true',
                        help='emit classification without compiling or running tests')
    parser.add_argument('paths', nargs='*', help='suite fragment paths (default: all suite files)')
    args = parser.parse_args()
    paths = args.paths or sorted(glob.glob('test/suite/*.lang'))
    if not paths:
        parser.error('no suite files')
    # Finish scanning before writing: unreadable inputs must fail the batch,
    # rather than silently running a partial manifest.
    records = [classify(path) for path in paths]
    sys.stdout.buffer.write(b''.join(field + b'\0' for record in records for field in record))


if __name__ == '__main__':
    main()
