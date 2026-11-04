#!/usr/bin/env python3
"""Measure LLVM emission separately from linking; retain commands and raw logs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import time
from gen import generate

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ['std/core.lang', 'out/version_info.lang', 'src/lexer.lang', 'src/parser.lang',
           'src/codegen.lang', 'src/codegen_llvm.lang', 'src/codegen_wasm.lang',
           'src/ast_emit.lang', 'src/sexpr_reader.lang', 'src/compiler_readers_none.lang', 'src/main.lang']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def measure(compiler, source, output, name, env, cwd=ROOT):
    ir = output / (name + '.ll')
    command = [str(compiler), *source, '-o', str(ir)]
    start = time.perf_counter()
    with (output / (name + '.stdout')).open('w') as stdout, (output / (name + '.stderr')).open('w') as stderr:
        # wait4 returns usage for this exact child, avoiding cumulative RUSAGE_CHILDREN
        # peaks from an earlier, larger run and any external time utility.
        child = subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout, stderr=stderr)
        _, status, usage = os.wait4(child.pid, 0)
        child.returncode = os.waitstatus_to_exitcode(status)
    elapsed = time.perf_counter() - start
    if child.returncode:
        raise RuntimeError(f'{name}: emit failed ({child.returncode}); see {name}.stderr')
    rss_kib = usage.ru_maxrss / 1024 if os.uname().sysname == 'Darwin' else usage.ru_maxrss
    return {'name': name, 'command': command, 'emit_seconds': elapsed,
            'user_seconds': usage.ru_utime, 'system_seconds': usage.ru_stime,
            'peak_rss_kib': int(rss_kib), 'ir_bytes': ir.stat().st_size,
            'ir_sha256': digest(ir), 'exit': child.returncode}


def pinned_build(root, compiler, output, label):
    receipt = root / 'out/build-receipt.json'
    command = ['python3', str(root / 'scripts/build_receipt.py'), 'check',
               '--input', str(receipt), '--compiler', str(compiler)]
    result = subprocess.run(command, cwd=root, capture_output=True)
    (output / (label + '-pin.stdout')).write_bytes(result.stdout)
    (output / (label + '-pin.stderr')).write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError(f'{label}: build receipt does not pin the current sources and compiler')
    return json.loads(receipt.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, default=ROOT / 'out/lang_next')
    parser.add_argument('--base-compiler', type=Path)
    parser.add_argument('--base-root', type=Path, help='clean checkout of the recorded base, with out/version_info.lang prepared')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sizes', type=int, nargs='+', default=[10000, 100000, 1000000])
    parser.add_argument('--self-runs', type=int, default=5)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    compiler = args.compiler.resolve()
    env = dict(os.environ, LANGBE='llvm', LANGOS='macos' if os.uname().sysname == 'Darwin' else 'linux',
               LANG_HOST_MAX_BYTES='134217728', LANG_HOST_MAX_NODES='16777216',
               LANG_CACHE=str(output / 'cache'))
    candidate_receipt = pinned_build(ROOT, compiler, output, 'candidate')
    report = {'candidate_build': candidate_receipt, 'compiler_sha256': digest(compiler), 'head': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'host': os.uname().nodename,
        'host_max_bytes': env['LANG_HOST_MAX_BYTES'], 'host_max_nodes': env['LANG_HOST_MAX_NODES'],
        'programs': [], 'self_compile': {},
        'full_scale_verdict': 'DEFERRED', 'self_compile_timing_verdict': 'DEFERRED'}
    try:
        for size in args.sizes:
            path = output / f'program-{size}.lang'
            with path.open('w') as stream:
                generate(size, stream)
            row = measure(compiler, [str(path)], output, f'program-{size}', env)
            row.update(lines=size, source_sha256=digest(path))
            report['programs'].append(row)
        by_size = {r['lines']: r for r in report['programs']}
        if 100000 in by_size and 1000000 in by_size:
            report['scale_ratio'] = by_size[1000000]['emit_seconds'] / by_size[100000]['emit_seconds']
            report['scale_pass'] = report['scale_ratio'] <= 15
            if 10000 in by_size:
                report['full_scale_verdict'] = 'PASS' if report['scale_pass'] else 'FAIL'
        if args.base_compiler or args.base_root:
            if not args.base_compiler or not args.base_root or args.self_runs != 5:
                parser.error('self comparison requires --base-compiler, --base-root and exactly 5 runs')
            base_root = args.base_root.resolve()
            base_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=base_root, text=True).strip()
            if base_head != '4b93dcaa32c177ed827fb7597b02d8431ace2dec':
                raise ValueError('base checkout is not the recorded base')
            if subprocess.check_output(['git', 'status', '--porcelain'], cwd=base_root, text=True):
                raise ValueError('base checkout must be clean')
            report['base_build'] = pinned_build(base_root, args.base_compiler.resolve(), output, 'base')
            report['base_head'] = base_head
            report['base_compiler_sha256'] = digest(args.base_compiler.resolve())
            for label, executable in [('base', args.base_compiler.resolve()), ('candidate', compiler)]:
                source_root = base_root if label == 'base' else ROOT
                sources = [str(source_root / s) for s in SOURCES]
                runs = [measure(executable, sources, output, f'self-{label}-{i}', env, cwd=source_root) for i in range(5)]
                report['self_compile'][label] = {'runs': runs, 'median_emit_seconds': statistics.median(r['emit_seconds'] for r in runs),
                    'source_hashes': {s: digest(source_root / s) for s in SOURCES}}
            report['self_ratio'] = report['self_compile']['candidate']['median_emit_seconds'] / report['self_compile']['base']['median_emit_seconds']
            report['self_pass'] = report['self_ratio'] <= 1.10
            report['self_compile_timing_verdict'] = 'PASS' if report['self_pass'] else 'FAIL'
    finally:
        (output / 'bench.json').write_text(json.dumps(report, indent=2) + '\n')
    if report.get('scale_pass') is False or report.get('self_pass') is False:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
