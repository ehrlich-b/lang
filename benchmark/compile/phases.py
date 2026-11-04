#!/usr/bin/env python3
"""Three fixed LLVM self-compiles, with exclusive process-CPU phase medians.

Use the development compiler from `make build`; clang/linking are not measured.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import statistics
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    'std/core.lang', 'out/version_info.lang', 'src/lexer.lang', 'src/parser.lang',
    'src/codegen.lang', 'src/codegen_llvm.lang', 'src/codegen_wasm.lang',
    'src/ast_emit.lang', 'src/sexpr_reader.lang',
    'src/compiler_readers_none.lang', 'src/main.lang',
)
PHASES = (
    'reading', 'tokens', 'parsing', 'expansion-registration',
    'type-checking-lowering-ir-emission', 'output',
)
RECORD = re.compile(r'^timing phase=(\S+) cpu_ms=(\d+\.\d{3}) count=(\d+)$')


def parse_timings(stderr):
    rows = {}
    for line in stderr.splitlines():
        if not line.startswith('timing '):
            continue
        match = RECORD.fullmatch(line)
        if not match or match[1] in rows or match[1] not in PHASES:
            raise ValueError(f'invalid or duplicate timing: {line}')
        rows[match[1]] = {'cpu_ms': float(match[2]), 'count': int(match[3])}
    if tuple(rows) != PHASES:
        raise ValueError(f'expected {PHASES}, received {tuple(rows)}')
    return rows


def children_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default=os.environ.get('COMPILER', 'out/lang_next'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    compiler = Path(args.compiler).resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, LANGBE='llvm', LANGOS='macos' if os.uname().sysname == 'Darwin' else 'linux')
    runs = []
    start = children_cpu()
    with tempfile.TemporaryDirectory(prefix='compile-phases-', dir=output.parent) as temp:
        for i in range(3):
            command = [str(compiler), 'compile', '--timings', *SOURCES, '-o', f'{temp}/self.ll']
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                    text=True, timeout=120, check=True)
            (output.parent / f'{output.stem}-run-{i + 1}.stderr').write_text(result.stderr)
            runs.append(parse_timings(result.stderr))
    cpu_seconds = children_cpu() - start
    if cpu_seconds >= 120:
        raise RuntimeError(f'three self-compiles exceeded 120 CPU seconds: {cpu_seconds:.3f}')
    medians = {}
    for phase in PHASES:
        counts = {run[phase]['count'] for run in runs}
        if len(counts) != 1:
            raise ValueError(f'input counts changed between runs: {phase}')
        medians[phase] = {'cpu_ms': statistics.median(run[phase]['cpu_ms'] for run in runs),
                          'count': counts.pop()}
    report = {'version': 1, 'compiler_sha256': hashlib.sha256(compiler.read_bytes()).hexdigest(),
              'sources': list(SOURCES), 'runs': runs, 'median': medians,
              'total_child_cpu_seconds': cpu_seconds}
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('phase | median CPU ms | input count')
    for phase, row in medians.items():
        print(f"{phase} | {row['cpu_ms']:.3f} | {row['count']}")
    print(f'three self-compiles: {cpu_seconds:.3f} CPU seconds; {output}')


if __name__ == '__main__':
    main()
