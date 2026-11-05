#!/usr/bin/env python3
"""Run one Scheme feature fixture, or the bounded-stack tail-call proof."""
import argparse
from pathlib import Path
import resource
import subprocess
from runner import compiler, compile_program, ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fixture', type=Path)
    p.add_argument('--evidence', required=True, type=Path)
    p.add_argument('--tail', action='store_true')
    p.add_argument('--refusal', action='store_true')
    args = p.parse_args()
    folder = args.evidence.resolve()
    cc = compiler(folder)
    if args.refusal:
        result = subprocess.run([str(cc), str(args.fixture), '-o', str(folder / 'refused.ll')],
                                cwd=ROOT, text=True, capture_output=True)
        (folder / 'refusal.log').write_text(result.stdout + result.stderr)
        assert result.returncode != 0
        assert 'scheme:3:2: call/cc:' in result.stderr, result.stderr
        print('PASS located call/cc refusal at 3:2')
        return
    for opt in (('0', '2') if args.tail else ('0',)):
        binary = compile_program(cc, args.fixture, folder, 'program-O' + opt, opt)
        def bounded_stack():
            resource.setrlimit(resource.RLIMIT_STACK, (262144, 262144))
        result = subprocess.run([str(binary)], text=True, capture_output=True,
                                timeout=180, preexec_fn=bounded_stack if args.tail else None)
        (folder / f'O{opt}.log').write_text(result.stdout + result.stderr)
        assert result.returncode == 0, (result.returncode, result.stderr)
        assert ('tail 10000000 ok' if args.tail else 'ok') in result.stdout, result.stdout
        print(f'PASS {args.fixture} O{opt}' + (' with 256 KiB stack' if args.tail else ''))


if __name__ == '__main__':
    main()
