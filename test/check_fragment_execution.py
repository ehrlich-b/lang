#!/usr/bin/env python3
"""Bounded local fragment checks with external command and CPU evidence."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
p = argparse.ArgumentParser()
p.add_argument('--evidence', type=Path, required=True)
a = p.parse_args()
base = a.evidence.resolve()
if base == ROOT or ROOT in base.parents:
    raise ValueError('evidence must be outside checkout')
base.mkdir(parents=True, exist_ok=True)
work = Path(tempfile.mkdtemp(prefix='fragments-', dir=base))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
rows = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv, timeout=8):
    import shutil
    argv = list(map(str, argv))
    inputs = {str(Path(x).resolve()): sha(x) for x in argv if Path(x).is_file()}
    executable = shutil.which(argv[0])
    if executable:
        inputs[str(Path(executable).resolve())] = sha(executable)
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        r = subprocess.run(argv, capture_output=True, timeout=timeout)
        status = dict(exit=r.returncode, timeout=False, stdout=r.stdout.hex(), stderr=r.stderr.hex())
    except subprocess.TimeoutExpired as e:
        status = dict(exit=None, timeout=True, stdout=(e.stdout or b'').hex(), stderr=(e.stderr or b'').hex())
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    rows.append(dict(argv=argv, inputs=inputs, **status,
                     cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime))
    (work / 'commands.json').write_text(json.dumps(rows, indent=2) + '\n')
    return status


def require(value, message):
    if not value:
        raise ValueError(message)


spec = importlib.util.spec_from_file_location('fragment', ROOT / 'scripts/fragment_exec.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
fixtures = ROOT / 'test/fragment_execution'
cache = work / 'cache'
arithmetic = work / 'arithmetic.ll'
r = run([ROOT / 'out/lang_next', fixtures / 'arithmetic.lang', '-o', arithmetic])
require(r['exit'] == 0, 'arithmetic compilation failed')
cli = [sys.executable, ROOT / 'scripts/fragment_exec.py']
checks = []
for ir in [arithmetic, fixtures / 'streams.ll', fixtures / 'failure.ll', fixtures / 'branch.ll']:
    cold = run([*cli, 'resolve', ir, '--cache', cache])
    require(json.loads(bytes.fromhex(cold['stdout']))[0] == 'lli', 'cold run did not retain lli')
    require(not cache.exists() or not list(cache.glob('*.json')), 'cold run populated cache')
    reference = run(['lli', *m.LLI_FLAGS, ir])
    cold_result = run([*cli, 'run', ir, '--cache', cache])
    require(reference == cold_result, 'cold execution differed')
    q = run([*cli, 'qualify', ir, '--cache', cache])
    require(q['exit'] == 0, 'qualification failed: ' + str(q))
    binary = bytes.fromhex(q['stdout']).decode().strip()
    warm = run([*cli, 'run', ir, '--cache', cache])
    require(warm == reference, 'warm exit or streams differed')
    resolved = run([*cli, 'resolve', ir, '--cache', cache])
    require(json.loads(bytes.fromhex(resolved['stdout'])) == [binary], 'warm resolution missed')
    value = m.identity(ir)
    require(m.lookup(cache, value) is not None, 'valid hit missed')
    for field in ['ir', 'clang', 'lli', 'linker', 'target', 'flags', 'lli_flags', 'oracle', 'runner', 'system', 'machine']:
        changed = copy.deepcopy(value)
        changed[field] = 'changed'
        require(m.lookup(cache, changed) is None, 'identity mutation hit: ' + field)
    # Copying qualification to a new key must not defeat the receipt comparison.
    changed = dict(value, oracle='changed')
    (cache / (m.key_for(changed) + '.json')).write_bytes((cache / (m.key_for(value) + '.json')).read_bytes())
    require(m.lookup(cache, changed) is None, 'stale receipt accepted')
    if ir == arithmetic:
        pairs = []
        for _ in range(5):
            require(run(['lli', *m.LLI_FLAGS, ir]) == run([binary]), 'benchmark output mismatch')
            pairs.append([rows[-2]['cpu_seconds'], rows[-1]['cpu_seconds']])
        medians = [statistics.median(pair[n] for pair in pairs) for n in range(2)]
        require(medians[1] <= .005, 'qualified arithmetic exceeded CPU target')
        (work / 'benchmark.json').write_text(json.dumps(dict(
            scope='resolved qualified binary; resolution excluded; not full runner latency',
            pairs_lli_native_cpu_seconds=pairs, medians=medians, target=.005), indent=2) + '\n')
    changed_ir = work / (ir.stem + '-changed.ll')
    changed_ir.write_bytes(ir.read_bytes() + b'\n; changed IR identity\n')
    resolved = run([*cli, 'resolve', changed_ir, '--cache', cache])
    require(json.loads(bytes.fromhex(resolved['stdout']))[0] == 'lli', 'changed IR hit stale binary')
    lli_only = work / ('lli-only-' + ir.stem)
    lli_only.mkdir()
    launcher = lli_only / 'lli'
    launcher.write_text('#!/bin/sh\nexec ' + m.tool('lli')['path'] + ' \"$@\"\n')
    launcher.chmod(0o700)
    without_clang = run(['/usr/bin/env', 'PATH=' + str(lli_only), *cli, 'run', ir, '--cache', cache])
    require(without_clang == reference, 'unavailable native toolchain broke lli fallback')
    damaged = work / ('corrupt-' + ir.stem)
    damaged.mkdir()
    (damaged / Path(binary).name).write_bytes(b'corrupt')
    receipt_name = m.key_for(value) + '.json'
    (damaged / receipt_name).write_bytes((cache / receipt_name).read_bytes())
    require(m.lookup(damaged, value) is None, 'corrupt binary accepted')
    require(run([*cli, 'run', ir, '--cache', damaged]) == reference, 'corrupt hit did not fall back')
    # Isolate each cold-run assertion without removing cache artifacts.
    cache = work / ('cache-' + ir.stem)
    checks.append(ir.name)

for name in ['timeout.ll', 'invalid.ll', 'assembly.ll', 'signal.ll']:
    ir = fixtures / name
    q = run([*cli, 'qualify', ir, '--cache', cache, '--timeout', '.3'])
    require(q['exit'] != 0, 'unsafe/failed qualification published: ' + name)
    require(not cache.exists() or not list(cache.glob('*.json')), 'failed qualification left a receipt')
    reference = run(['lli', *m.LLI_FLAGS, ir], timeout=.3)
    if name == 'timeout.ll':
        actual = run([*cli, 'run', ir, '--cache', cache], timeout=.7)
        require(reference['timeout'] and actual['timeout'], 'timeout behavior changed')
    elif name == 'invalid.ll':
        require(run([*cli, 'run', ir, '--cache', cache]) == reference, 'invalid IR fallback differed')
    checks.append(name)
(work / 'summary.json').write_text(json.dumps(dict(status='PASS', checks=checks,
    affinity=sorted(os.sched_getaffinity(0)), memory_limit=resource.getrlimit(resource.RLIMIT_AS),
    headless='CLI only; no browser', commands='commands.json'), indent=2) + '\n')
print('PASS fragment execution:', work)
