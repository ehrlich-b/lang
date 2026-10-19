#!/usr/bin/env python3
"""Observe the native-reader boundary; never change production limits or phases."""
import argparse
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import time

from oracle import digest, run, save

ROOT = Path(__file__).resolve().parents[2]
FIX = Path('conformance/zig/fixtures')


def bounded_output(command, env, log, limit, timeout):
    start = time.monotonic()
    with open(log, 'wb') as error:
        child = subprocess.Popen(list(map(str, command)), cwd=ROOT, env=env,
                                 stdout=subprocess.PIPE, stderr=error, start_new_session=True)
        selector = selectors.DefaultSelector()
        selector.register(child.stdout, selectors.EVENT_READ)
        output = bytearray()
        outcome = None
        try:
            while outcome is None:
                remaining = timeout - (time.monotonic() - start)
                if remaining <= 0 or not selector.select(remaining):
                    outcome = 'timeout'
                    break
                data = os.read(child.stdout.fileno(), min(65536, limit + 1 - len(output)))
                if not data:
                    code = child.wait(timeout=max(0.01, remaining))
                    outcome = 'pass' if code == 0 else 'runtime_failure'
                    break
                output.extend(data)
                if len(output) > limit:
                    outcome = 'output_limit'
        except subprocess.TimeoutExpired:
            outcome = 'timeout'
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            child.stdout.close()
            selector.close()
    return {'outcome': outcome, 'bytes_observed': len(output), 'limit': limit,
            'seconds': time.monotonic() - start, 'command': list(map(str, command))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    compiler, work = args.compiler.resolve(), args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, LANGBE='llvm', LANG_CACHE=str(work / 'cache'), TMPDIR=str(work))
    report = {'production_changes': False, 'upstream_credit': 0, 'probes': []}
    paths = ['src/limits.lang', 'src/codegen.lang', 'src/codegen_llvm.lang',
             'src/main.lang', 'src/reader_main.lang', 'src/sexpr_reader.lang',
             'src/parser.lang', 'src/ast_emit.lang']
    before = {p: digest(ROOT / p) for p in paths}
    report['production_source_sha256'] = before
    report['declared_limits'] = {key: int(value) for key, value in re.findall(
        r'var ((?:LIMIT|SIZE)_\w+) i64 = (\d+);', (ROOT / 'src/limits.lang').read_text())}
    result = run([compiler, FIX / 'recursive.lang', '-o', work / 'recursive.ll'],
                 work / 'recursive-compile.txt', 120, env, ROOT)
    report['probes'].append(dict(name='recursive_helper_and_second_reader', **result))
    if result['outcome'] != 'pass':
        save(args.receipt, report)
        raise SystemExit('recursive reader failed')
    for opt in [0, 2]:
        result = run(['clang', f'-O{opt}', work / 'recursive.ll', '-o', work / f'recursive-O{opt}'],
                     work / f'link-O{opt}.txt', 120, env, ROOT)
        if result['outcome'] != 'pass':
            raise SystemExit('reader probe link failed')
        result = run([work / f'recursive-O{opt}'], work / f'run-O{opt}.txt', 10, env, ROOT)
        # This program's contract is exit 42, not the normal test-runner exit 0.
        result['outcome'] = 'pass' if result['returncode'] == 42 else 'wrong_answer'
        report['probes'].append(dict(name=f'native_O{opt}', **result))
    result = run([compiler, 'read', FIX / 'file_origin.lang', FIX / 'input.boundary_file',
                  '-o', work / 'origin.ast'], work / 'origin-read.txt', 120, env, ROOT)
    report['probes'].append(dict(name='serialized_origin', **result))
    if result['outcome'] != 'pass' or '(span 0 1 ' not in (work / 'origin.ast').read_text():
        raise SystemExit('reader lost serialized span')
    result = run([compiler, '--from-ast', work / 'origin.ast', '--ast-source',
                  FIX / 'input.boundary_file', '-o', work / 'invalid.ll'],
                 work / 'origin-diagnostic.txt', 120, env, ROOT)
    diagnostic = (work / 'origin-diagnostic.txt').read_text()
    result['source_location_preserved'] = 'input.boundary_file:1:1:' in diagnostic
    report['probes'].append(dict(name='guest_origin_rejection', **result))
    result = bounded_output([compiler, 'read', '--compact', FIX / 'output_limit.lang',
                             FIX / 'input.boundary_oversize'], env,
                            work / 'output-limit.txt', 1024, 120)
    report['probes'].append(dict(name='oversized_output_rejected_by_host_harness', **result))
    preparation = run([compiler, 'read', FIX / 'input_limit.lang', FIX / 'input.boundary_length',
                       '-o', work / 'length.ast'], work / 'length-prepare.txt', 120, env, ROOT)
    report['input_limit_inventory'] = {'preparation': preparation, 'measurements': []}
    if preparation['outcome'] == 'pass':
        executable = work / 'cache/readers/boundary_length'
        for size in [4194302, 4194303, 4194304, 4194308]:
            observed = subprocess.run([str(executable)], input=b'x' * size, capture_output=True,
                                      env=env, cwd=ROOT, timeout=10)
            (work / f'length-{size}.ast').write_bytes(observed.stdout)
            (work / f'length-{size}.stderr').write_bytes(observed.stderr)
            match = re.search(rb'\(number (\d+)\)', observed.stdout)
            report['input_limit_inventory']['measurements'].append(
                {'input_bytes': size, 'reader_observed_bytes': int(match[1]) if match else None,
                 'returncode': observed.returncode})
            report['input_limit_inventory']['measurements'][-1].update(
                stdout_empty=not observed.stdout,
                overflow_diagnostic=b'size limit exceeded: reader stdin' in observed.stderr)
    report['production_source_unchanged'] = before == {p: digest(ROOT / p) for p in paths}
    save(args.receipt, report)
    good = all(p['outcome'] == 'pass' for p in report['probes'][:4])
    good &= report['probes'][4]['outcome'] == 'compile_failure'
    good &= report['probes'][4]['source_location_preserved']
    good &= report['probes'][5]['outcome'] == 'output_limit'
    measurements = report['input_limit_inventory']['measurements']
    good &= len(measurements) == 4 and all(
        (r['returncode'] == 0 and r['reader_observed_bytes'] == r['input_bytes'])
        if r['input_bytes'] < 4194304 else
        (r['returncode'] == 1 and r['stdout_empty'] and r['overflow_diagnostic'])
        for r in measurements)
    if not good or not report['production_source_unchanged']:
        raise SystemExit('reader boundary probe failed; see receipt')


if __name__ == '__main__':
    main()
