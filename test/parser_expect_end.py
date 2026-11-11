#!/usr/bin/env python3
"""Run the small end-check fixture and assert its rendered diagnostics."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    scratch = root.parent / 'scratch'
    scratch.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='parser-expect-end-', dir=scratch))
    print(f'work: {work}', flush=True)
    host_os = 'macos' if os.uname().sysname == 'Darwin' else 'linux'
    env = dict(os.environ, LANGBE='llvm', LANGOS=host_os, LANG_CACHE=str(work / 'cache'))

    def run(command):
        print('command:', ' '.join(map(str, command)), flush=True)
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
        print(result.stdout, end='', flush=True)
        print(result.stderr, end='', flush=True)
        if result.returncode:
            raise SystemExit(f'command failed with exit {result.returncode}')
        return result

    run([str(args.compiler.resolve()), 'test/suite/294_parser_expect_end.lang',
         '-o', str(work / 'fixture.ll')])
    result = run(['lli', str(work / 'fixture.ll')])
    expected = ("missing-equals:2:9: expected '=', found 4 @14:15\n"
                "trailing-token:2:1: expected end of input, found ! @6:7\n")
    if result.stdout or result.stderr != expected:
        raise SystemExit(f'wrong diagnostic output; expected {expected!r}')
    print('PASS: exact diagnostics, spans, EOF, supplied stream and earlier mismatch')


if __name__ == '__main__':
    main()
