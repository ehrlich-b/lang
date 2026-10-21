#!/usr/bin/env python3
"""Bounded contract corpus with negative controls; does not qualify isolation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / 'test/confinement/worker_cases.json'
WORKER = ROOT / 'test/confinement/worker_attack.py'
AUTHORITY = {'filesystem-read', 'filesystem-write', 'environment', 'network',
             'process', 'inherited-descriptor'}
PUBLICATION = {'stale-request', 'superseded-generation', 'cancel-before-publication',
               'partial-failure', 'current-response'}


def load_contract():
    data = json.loads(CASES.read_text())
    assert data['version'] == 1
    assert len({r['id'] for r in data['cases']}) == len(data['cases']) == 19
    context = data['C']
    for grant in context['granted_inputs'].values():
        assert hashlib.sha256(grant['utf8'].encode()).hexdigest() == grant['sha256']
        assert len(grant['utf8'].encode()) <= context['budgets']['input_bytes']
    accounts = set(context['budgets']) | {'granted_inputs', 'request_id',
                                        'generation', 'cancellation', 'publication'}
    assert {r['attack'] for r in data['cases']} == AUTHORITY | PUBLICATION | {
        'input', 'spin', 'stdout', 'stderr', 'combined', 'exact',
        'cancel-before-start', 'cancel-running'}
    for row in data['cases']:
        assert row['C_accounts'] and set(row['C_accounts']) <= accounts
        assert row['granted_inputs'] == ['source']
    return data


def publish(context, response, cancelled, permissive):
    """Reference publication model, deliberately separate from fixture oracle."""
    if not permissive:
        if cancelled:
            return 'cancelled', b''
        if (response['request_id'], response['generation']) != (
                context['request_id'], context['generation']):
            return 'stale-response', b''
        if response['status'] != 0:
            return 'worker-failed', b''
    return 'complete', response['payload']


def publication_case(context, attack, permissive):
    # Deterministic event order: start, complete/cancel/supersede, then delivery.
    response = dict(request_id=context['request_id'], generation=context['generation'],
                    status=0, payload=b'granted')
    cancelled = False
    events = ['start', 'worker-complete']
    if attack == 'stale-request':
        response['request_id'] = 'request-1'
        events.append('new-request')
    elif attack == 'superseded-generation':
        response['generation'] -= 1
        events.append('new-generation')
    elif attack == 'cancel-before-publication':
        cancelled = True
        events.append('cancel')
    elif attack == 'partial-failure':
        response['status'] = 7
        events.append('worker-failed')
    events.append('deliver')
    status, payload = publish(context, response, cancelled, permissive)
    return dict(status=status, published_bytes=len(payload), launched=False,
                published_sha256=hashlib.sha256(payload).hexdigest(), reaped=True, events=events)


def stop_group(process):
    # All workers, including the single process-access control, share a new
    # process group. Reap the leader and terminate descendants on every path.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=2)


def execute(context, attack, profile, folder):
    permissive = profile == 'permissive'
    if profile == 'native-unavailable':
        return dict(status='isolation-unavailable', published_bytes=0,
                    launched=False, reaped=True)
    if attack in PUBLICATION:
        return publication_case(context, attack, permissive)
    if attack == 'cancel-before-start' and not permissive:
        return dict(status='cancelled', published_bytes=0, launched=False, reaped=True)
    if attack == 'cancel-before-start':
        attack = 'input'
    secret = folder / 'private-fixture'
    secret.write_bytes(b'disposable private bytes')
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(4)
    fd = os.open(secret, os.O_RDONLY)
    process = None
    budget = context['budgets']
    captured = {'stdout': bytearray(), 'stderr': bytearray()}
    started = time.monotonic()
    status = None
    try:
        command = [sys.executable, str(WORKER), attack, profile, str(secret),
                   str(listener.getsockname()[1]), str(fd)]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True,
                                   pass_fds=(fd,), env=dict(os.environ,
                                   CONFINEMENT_DISPOSABLE_ENV='ambient-value'))
        process.stdin.write(context['granted_inputs']['source']['utf8'].encode())
        process.stdin.close()
        with selectors.DefaultSelector() as selector:
            for name in captured:
                stream = getattr(process, name)
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            while selector.get_map():
                elapsed = time.monotonic() - started
                # The outer watchdog is independent of the host under test.
                # Hitting it is a corpus failure, never an expected deadline.
                if elapsed > 3:
                    status = 'harness-watchdog'
                    break
                if not permissive and elapsed * 1000 >= budget['wall_ms']:
                    status = 'deadline-exceeded'
                    break
                for key, _ in selector.select(.01):
                    chunk = os.read(key.fileobj.fileno(), 2048)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    captured[key.data].extend(chunk)
                    total = sum(map(len, captured.values()))
                    if total > 8192:
                        status = 'harness-output-cap'
                        break
                    if not permissive and total > budget['output_bytes']:
                        status = 'output-limit'
                        break
                    if (attack == 'cancel-running' and not permissive
                            and b'READY\n' in captured['stderr']):
                        status = 'cancelled'
                        break
                if status:
                    break
        if status is None:
            code = process.wait(timeout=1)
            if code:
                status = 'worker-failed'
            elif attack in AUTHORITY:
                status = captured['stdout'].decode().strip()
            else:
                status = 'complete'
    finally:
        if process:
            stop_group(process)
            process.stdout.close()
            process.stderr.close()
        listener.close()
        os.close(fd)
    for name, payload in captured.items():
        (folder / (name + '.bin')).write_bytes(payload)
    payload = captured['stdout'] if status == 'complete' else b''
    return dict(status=status, published_bytes=len(payload),
                published_sha256=hashlib.sha256(payload).hexdigest(),
                captured_bytes=sum(map(len, captured.values())), launched=True,
                reaped=process.returncode is not None, elapsed_ms=round((time.monotonic()-started)*1000))


def run(data, profile, output):
    output.mkdir(parents=True)
    rows = []
    for case in data['cases']:
        folder = output / case['id']
        folder.mkdir()
        observation = execute(data['C'], case['attack'], profile, folder)
        expected_bytes = case.get('expected_bytes', 0)
        passed = (observation['status'] == case['expected']
                  and observation['published_bytes'] == expected_bytes and observation['reaped'])
        if 'expected_sha256' in case:
            passed = passed and observation.get('published_sha256') == case['expected_sha256']
        row = dict(id=case['id'], expected=case['expected'], expected_bytes=expected_bytes,
                   observed=observation, passed=passed)
        rows.append(row)
        print(f"{profile}: {case['id']}: {'PASS' if passed else 'FAIL'} "
              f"expected={case['expected']} observed={observation['status']}", flush=True)
    receipt = dict(version=1, host=profile, scope=data['scope'],
                   qualification=False, production_admission=False, trusted_native_fallback=False,
                   admission='isolation-unavailable' if profile == 'native-unavailable' else 'test-only',
                   passed=all(r['passed'] for r in rows), rows=rows)
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def self_test(data, output):
    model = run(data, 'policy-model', output / 'policy-model')
    negatives = []
    for profile in ['permissive', 'native-unavailable']:
        destination = output / profile
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                 '--host', profile, '--output', str(destination)], timeout=30)
        assert result.returncode == 1, f'{profile} must fail the command-line corpus'
        receipts = list(destination.glob('worker-corpus-*/' + profile + '/receipt.json'))
        assert len(receipts) == 1
        negatives.append(json.loads(receipts[0].read_text()))
    permissive, unavailable = negatives
    assert model['passed'], 'reference contract model failed'
    failures = {r['id'] for r in permissive['rows'] if not r['passed']}
    # Mutation control: each unsafe policy change must be detected, including
    # each authority probe, both cancellation points and each stale identity.
    assert failures == {r['id'] for r in data['cases']} - {
        'granted-input', 'exact-output', 'current-response'}
    assert not permissive['passed']
    assert not unavailable['passed'] and unavailable['admission'] == 'isolation-unavailable'
    assert all(not r['observed']['launched'] and r['observed']['status'] == 'isolation-unavailable'
               for r in unavailable['rows'])
    assert all(not r['production_admission'] and not r['qualification']
               and not r['trusted_native_fallback'] for r in [model, permissive, unavailable])
    print('PASS corpus controls; native admission FAIL isolation-unavailable; no qualification')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=['policy-model', 'permissive', 'native-unavailable'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check-contract', action='store_true')
    args = parser.parse_args()
    data = load_contract()
    if args.check_contract:
        for row in data['cases']:
            print(f"{row['id']}: C={','.join(row['C_accounts'])}; "
                  f"grants={','.join(row['granted_inputs'])}; expected={row['expected']}")
        assert (ROOT / 'docs/WORKER_CORPUS.md').is_file()
        print('PASS 19 case mappings; test-only context, no production admission')
        return 0
    if args.output is None:
        parser.error('--output is required for execution')
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('evidence must be outside the checkout')
    # Retain every run. Readiness may execute the exact command repeatedly.
    output.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix='worker-corpus-', dir=output))
    print(f'evidence: {run_dir}', flush=True)
    if args.host:
        return 0 if run(data, args.host, run_dir / args.host)['passed'] else 1
    self_test(data, run_dir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
