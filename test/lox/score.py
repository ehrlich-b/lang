#!/usr/bin/env python3
"""Score an executable against the pinned Crafting Interpreters clox suite."""
import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--suite', required=True, type=Path, help='Crafting Interpreters checkout')
parser.add_argument('--interpreter', required=True, help='executable taking a Lox file')
args = parser.parse_args()
counts = Counter()
passed = Counter()
for path in sorted((args.suite / 'test').rglob('*.lox')):
    rel = path.relative_to(args.suite / 'test')
    if rel.parts[0] in ('benchmark', 'scanning', 'expressions'):
        continue
    lines = path.read_text().splitlines()
    if any('// nontest' in line for line in lines):
        continue
    output, errors, runtime = [], set(), None
    for number, line in enumerate(lines, 1):
        if m := re.search(r'// expect: ?(.*)', line):
            output.append(m[1])
        elif m := re.search(r'// (Error.*)', line):
            errors.add((number, m[1]))
        elif m := re.search(r'// \[((java|c) )?line (\d+)\] (Error.*)', line):
            if m[2] in (None, 'c'):
                errors.add((int(m[3]), m[4]))
        elif m := re.search(r'// expect runtime error: (.+)', line):
            runtime = (number, m[1])
    counts[rel.parts[0]] += 1
    try:
        result = subprocess.run([args.interpreter, str(path)], capture_output=True, text=True, timeout=30)
        stderr = result.stderr.splitlines()
        ok = result.stdout.splitlines() == output
        if runtime:
            stack = next((m for line in stderr[1:] if (m := re.search(r'\[line (\d+)\]', line))), None)
            ok &= result.returncode == 70 and bool(stderr) and stderr[0] == runtime[1] and stack is not None and int(stack[1]) == runtime[0]
        else:
            actual = set()
            for line in stderr:
                m = re.search(r'\[.*line (\d+)\] (Error.+)', line)
                if m:
                    actual.add((int(m[1]), m[2]))
                elif line:
                    ok = False
            ok &= result.returncode == (65 if errors else 0) and actual == errors
    except (OSError, subprocess.TimeoutExpired) as exc:
        ok = False
        print(f'{rel}: {exc}', file=sys.stderr)
    if ok:
        passed[rel.parts[0]] += 1
    else:
        print(f'FAIL {rel}')
for group in sorted(counts):
    print(f'{group}: {passed[group]}/{counts[group]}')
print(f'TOTAL {sum(passed.values())}/{sum(counts.values())}')
sys.exit(0 if sum(passed.values()) == sum(counts.values()) == 246 else 1)
