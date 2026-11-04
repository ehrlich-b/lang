#!/usr/bin/env python3
"""Generate an exact number of nonblank Lang source lines, deterministically."""
import argparse
from pathlib import Path


def generate(lines, output):
    if lines < 36:
        raise ValueError('at least 36 lines are required')
    groups, extra = divmod(lines - 4, 32)
    for i in range(groups):
        output.write(f'struct S{i} {{\n a i64;\n b i64;\n}}\n')
        output.write(f'func work{i}(x i64) i64 {{\n var p S{i};\n p.a = x;\n p.b = 1;\n')
        value = f'work{i-1}(p.a + p.b)' if i else 'p.a + p.b'
        output.write(f' var v i64 = {value};\n')
        output.write(' v = v + 1;\n' * 21)
        output.write(' return v;\n}\n')
    output.write('func main() i64 {\n')
    for i in range(extra):
        output.write(f' var pad{i} i64 = {i};\n')
    output.write(f' if work{groups-1}(0) != {groups * 22} {{ return 1; }}\n return 0;\n}}\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lines', type=int, required=True)
    parser.add_argument('-o', '--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('w') as output:
        generate(args.lines, output)


if __name__ == '__main__':
    main()
