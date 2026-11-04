#!/usr/bin/env python3
"""Paired native benchmarks. Smoke checks are correctness checks, never perf verdicts."""
import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
SOURCES = Path(__file__).resolve().parent
BASE = '4b93dcaa32c177ed827fb7597b02d8431ace2dec'
NOT_BEFORE = datetime(2026, 11, 6, 18, 27, tzinfo=ZoneInfo('America/New_York'))
FLAGS = ['-O2', '-ffp-contract=off']
RUNS = 5


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(args, env=None):
    print('+', ' '.join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, capture_output=True,
                          timeout=300, cwd=ROOT, env=env)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def measure(compiler, output, smoke):
    manifest = json.loads((SOURCES / 'workloads.json').read_text())
    output.mkdir(parents=True, exist_ok=True)
    rows = {}
    compiler_hash = sha(compiler)
    for name, settings in manifest.items():
        lang, c = SOURCES / (name + '.lang'), SOURCES / (name + '.c')
        source_hashes = {'lang': sha(lang), 'c': sha(c)}
        ir = output / (name + '.ll')
        binaries = {kind: output / (name + '-' + kind) for kind in ('lang', 'c')}
        env = dict(os.environ, LANGBE='llvm', LANGOS='linux',
                   LANG_CACHE=str(output / 'cache'))
        command([compiler, lang.relative_to(ROOT), '-o', ir], env)
        command(['clang', *FLAGS, ir, '-o', binaries['lang']])
        command(['clang', *FLAGS, c, '-o', binaries['c']])
        size = settings['smoke_size' if smoke else 'size']
        samples = {'lang': [], 'c': []}
        outputs = {'lang': [], 'c': []}
        for trial in range(1 if smoke else RUNS):
            # Alternate order to reduce systematic first/second-run bias.
            for kind in (('lang', 'c') if trial % 2 == 0 else ('c', 'lang')):
                start = time.perf_counter_ns()
                result = command([binaries[kind], size])
                elapsed = (time.perf_counter_ns() - start) / 1e9
                outputs[kind].append(result.stdout.decode('ascii'))
                samples[kind].append(elapsed)
                if result.stderr:
                    raise RuntimeError(f'{name}/{kind} wrote stderr: {result.stderr!r}')
        reference = outputs['c'][0]
        if any(value != reference for values in outputs.values() for value in values):
            raise RuntimeError(f'{name}: output mismatch {outputs}')
        if smoke and reference != settings['smoke_output']:
            raise RuntimeError(f'{name}: expected {settings["smoke_output"]!r}, got {reference!r}')
        if source_hashes != {'lang': sha(lang), 'c': sha(c)}:
            raise RuntimeError(f'{name}: source changed during execution')
        row = {'size': size, 'output': reference,
               'source_sha256': source_hashes,
               'ir_sha256': sha(ir)}
        if not smoke:
            row['samples_seconds'] = samples
            row['median_seconds'] = {k: statistics.median(v) for k, v in samples.items()}
            row['ratio_lang_over_c'] = row['median_seconds']['lang'] / row['median_seconds']['c']
        rows[name] = row
    if sha(compiler) != compiler_hash:
        raise RuntimeError('compiler changed during execution')
    data = {'status': 'SMOKE_ONLY' if smoke else 'MEASURED',
            'compiler_sha256': compiler_hash, 'base': BASE,
            'head': command(['git', 'rev-parse', 'HEAD']).stdout.decode().strip(),
            'clang': command(['clang', '--version']).stdout.decode(),
            'flags': FLAGS, 'runs': 1 if smoke else RUNS,
            'host': platform.node(), 'machine': platform.machine(),
            'timestamp': datetime.now().astimezone().isoformat(),
            'workloads_sha256': sha(SOURCES / 'workloads.json'), 'workloads': rows}
    if not smoke:
        data['geometric_mean_lang_over_c'] = math.exp(statistics.mean(
            math.log(row['ratio_lang_over_c']) for row in rows.values()))
        data['verdict'] = 'PASS' if data['geometric_mean_lang_over_c'] <= 1.15 else 'FAIL'
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--compiler-sha256', required=True)
    parser.add_argument('--baseline-compiler', type=Path)
    parser.add_argument('--baseline-sha256')
    parser.add_argument('--output-dir', type=Path, required=True,
                        help='Evidence directory outside the checkout')
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    compiler = args.compiler.resolve()
    output = args.output_dir.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('evidence must be outside the checkout')
    if sha(compiler) != args.compiler_sha256:
        parser.error('candidate compiler hash mismatch')
    if not args.smoke:
        if datetime.now(NOT_BEFORE.tzinfo) < NOT_BEFORE:
            parser.error('DEFERRED: full measurement is permitted after ' + NOT_BEFORE.isoformat())
        if not args.baseline_compiler or not args.baseline_sha256:
            parser.error('full runs require the pinned baseline compiler and its SHA-256')
        baseline = args.baseline_compiler.resolve()
        if sha(baseline) != args.baseline_sha256:
            parser.error('baseline compiler hash mismatch')
        if any((output / name).exists() for name in ('perf-before.json', 'perf.json')):
            parser.error('preserve the original measurements; use a fresh evidence directory')
        before = measure(baseline, output / 'base', False)
        before['role'] = 'baseline'
        write_json(output / 'perf-before.json', before)
    result = measure(compiler, output / ('smoke' if args.smoke else 'candidate'), args.smoke)
    result['role'] = 'candidate'
    if args.smoke:
        result['full_run'] = 'DEFERRED'
        result['not_before'] = NOT_BEFORE.isoformat()
    else:
        for name, row in result['workloads'].items():
            if row['source_sha256'] != before['workloads'][name]['source_sha256']:
                raise RuntimeError(f'{name}: baseline/candidate source identity mismatch')
            if row['output'] != before['workloads'][name]['output']:
                raise RuntimeError(f'{name}: baseline/candidate output mismatch')
    write_json(output / ('smoke.json' if args.smoke else 'perf.json'), result)
    print('SMOKE_ONLY; full performance verdict DEFERRED' if args.smoke else result['verdict'])
    return 0 if args.smoke or result['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
