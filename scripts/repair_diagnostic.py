#!/usr/bin/env python3
"""Demonstrate one bounded repair: insert a missing return semicolon.

This deliberately recognizes one known fixture correction. It does not execute
compiler messages or generalize them into edits. All offsets are byte offsets.
"""
import argparse
import json
from pathlib import Path
import subprocess


def compile_source(compiler, source, output):
    return subprocess.run([str(compiler), '--diagnostics=json', str(source),
                           '-o', str(output)], capture_output=True, timeout=30)


def repair(compiler, source, output):
    before = source.read_bytes()
    failed = compile_source(compiler, source, output)
    if failed.returncode == 0:
        raise ValueError('expected the known missing-semicolon failure')
    diagnostics = [json.loads(line) for line in failed.stderr.splitlines()]
    candidates = [d for d in diagnostics if d['version'] == 1 and
                  d['severity'] == 'error' and d['code'] == 'syntax-error' and
                  d['path'] == str(source) and
                  "expected ';' after return" in d['message']]
    if len(candidates) != 1:
        raise ValueError('expected exactly one recognized diagnostic')
    span = candidates[0]['span']
    start, end = span['start'], span['end']
    if not (0 <= start < end <= len(before)) or before[start:end] != b'}':
        raise ValueError('diagnostic does not locate the expected closing brace')
    after = before[:start] + b'; ' + before[start:]
    source.write_bytes(after)
    success = compile_source(compiler, source, output)
    if success.returncode or success.stderr:
        raise ValueError('repair did not compile cleanly: ' + repr(success.stderr))
    return {'span': span, 'before': before[start:end].decode(),
            'inserted': '; ', 'compiler_exit': success.returncode}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('compiler', type=Path)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(repair(args.compiler.resolve(), args.source.resolve(),
                            args.output.resolve())))
