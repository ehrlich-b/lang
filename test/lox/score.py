#!/usr/bin/env python3
"""Score native clox or a Lox runner with source-located diagnostics."""
import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys


@dataclass(frozen=True)
class Diagnostic:
    line: int
    column: int
    message: str


def located_diagnostics(path, stderr):
    """Read located diagnostic triples and check their source and byte ranges."""
    source = path.read_bytes()
    lines = source.split(b'\n')
    rendered = stderr.split('\n')
    if rendered and rendered[-1] == '':
        rendered.pop()
    if not rendered or len(rendered) % 3:
        return []
    diagnostics = []
    header = re.compile(re.escape(str(path)) + r':([1-9]\d*):([1-9]\d*): (.+) @(\d+):(\d+)')
    for number in range(0, len(rendered), 3):
        match = header.fullmatch(rendered[number])
        if not match:
            return []
        line, column = int(match[1]), int(match[2])
        start, end = int(match[4]), int(match[5])
        if not 0 <= start <= end <= len(source):
            return []
        if line != source.count(b'\n', 0, start) + 1:
            return []
        if column != start - source.rfind(b'\n', 0, start):
            return []
        if rendered[number + 1] != lines[line - 1].removesuffix(b'\r').decode('utf-8'):
            return []
        marker = rendered[number + 2]
        if not re.fullmatch(r'[ \t]*\^+', marker):
            return []
        source_line = rendered[number + 1]
        if source_line.isascii():
            prefix = source_line[:column - 1]
            padding = ''.join('\t' if char == '\t' else ' ' for char in prefix)
            through_span = source_line[:column - 1 + end - start]
            carets = max(1, len(through_span.expandtabs(8)) - len(prefix.expandtabs(8)))
            if marker != padding + '^' * carets:
                return []
        diagnostics.append(Diagnostic(line, column, match[3]))
    return diagnostics


def expectations(path):
    output, errors, runtime = [], set(), None
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if '// nontest' in line:
            return None
        if match := re.search(r'// expect: ?(.*)', line):
            output.append(match[1])
        elif match := re.search(r'// (Error.*)', line):
            errors.add((number, match[1]))
        elif match := re.search(r'// \[((java|c) )?line (\d+)\] (Error.*)', line):
            if match[2] in (None, 'c'):
                errors.add((int(match[3]), match[4]))
        elif match := re.search(r'// expect runtime error: (.+)', line):
            runtime = (number, match[1])
    return output, errors, runtime


def clox_matches(result, errors, runtime):
    stderr = result.stderr.splitlines()
    if runtime:
        frames = [re.fullmatch(r'\[line (\d+)\] in (?:script|[^\s]+\(\))', line) for line in stderr[1:]]
        return (result.returncode == 70 and len(stderr) >= 2 and stderr[0] == runtime[1]
                and all(frames) and int(frames[0][1]) == runtime[0])

    actual = set()
    for line in stderr:
        match = re.search(r'\[.*line (\d+)\] (Error.+)', line)
        if match:
            actual.add((int(match[1]), match[2]))
        elif line:
            return False
    return result.returncode == (65 if errors else 0) and actual == errors


def crashed(result):
    return (result.returncode < 0 or result.returncode >= 128
            or re.search(r'PLEASE submit a bug report|LLVM ERROR|Broken (?:module|function)|'
                         r'Segmentation fault|\bAborted\b|Assertion .* failed',
                         result.stderr, re.IGNORECASE) is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', required=True, type=Path, help='Crafting Interpreters checkout')
    parser.add_argument('--interpreter', required=True, help='executable taking a Lox file')
    parser.add_argument('--located', action='store_true', help='require located diagnostic triples')
    parser.add_argument('--minimum', type=int, default=246)
    args = parser.parse_args()
    counts, passed = Counter(), Counter()
    crashes = unlocated = execution_errors = runtime_mismatches = 0
    for path in sorted((args.suite / 'test').rglob('*.lox')):
        rel = path.relative_to(args.suite / 'test')
        if rel.parts[0] in ('benchmark', 'scanning', 'expressions'):
            continue
        expected = expectations(path)
        if expected is None:
            continue
        output, errors, runtime = expected
        counts[rel.parts[0]] += 1
        try:
            result = subprocess.run([args.interpreter, str(path)], capture_output=True,
                                    text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as exc:
            execution_errors += 1
            print(f'EXECUTION ERROR {rel}: {exc}', file=sys.stderr)
            print(f'FAIL {rel}')
            continue
        ok = result.stdout.splitlines() == output
        if args.located:
            if crashed(result):
                crashes += 1
                print(f'CRASH {rel}: exit {result.returncode}\n{result.stderr}')
            diagnostics = located_diagnostics(path, result.stderr)
            if result.returncode != 0 and not diagnostics:
                unlocated += 1
                print(f'UNLOCATED {rel}: exit {result.returncode}\n{result.stderr}')
            actual = [(d.line, d.message) for d in diagnostics]
            if runtime:
                runtime_matches = result.returncode == 70 and actual == [runtime]
                if not runtime_matches:
                    runtime_mismatches += 1
                    print(f'RUNTIME ERROR MISMATCH {rel}: exit {result.returncode}\n{result.stderr}')
                ok &= runtime_matches
            elif errors:
                ok &= result.returncode == 65 and set(actual) == errors
            else:
                ok &= result.returncode == 0 and not result.stderr
        else:
            ok &= clox_matches(result, errors, runtime)
        if ok:
            passed[rel.parts[0]] += 1
        else:
            print(f'FAIL {rel}')
    for group in sorted(counts):
        print(f'{group}: {passed[group]}/{counts[group]}')
    if args.located:
        print(f'CRASHES {crashes}\nUNLOCATED {unlocated}\nEXECUTION ERRORS {execution_errors}')
        print(f'RUNTIME ERROR MISMATCHES {runtime_mismatches}')
    print(f'TOTAL {sum(passed.values())}/{sum(counts.values())}')
    return int(sum(counts.values()) != 246 or sum(passed.values()) < args.minimum
               or crashes != 0 or unlocated != 0 or execution_errors != 0
               or runtime_mismatches != 0)


if __name__ == '__main__':
    sys.exit(main())
