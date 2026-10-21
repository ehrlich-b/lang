#!/usr/bin/env python3
"""Bounded contract corpus with negative controls; does not qualify isolation."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import struct
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


def require(condition, message="invalid corpus contract"):
    if not condition:
        raise RuntimeError(message)


def load_contract():
    data = json.loads(CASES.read_text())
    require(data['version'] == 1, 'invalid corpus contract')
    require(len({r['id'] for r in data['cases']}) == len(data['cases']) == 20, 'invalid corpus contract')
    context = data['C']
    for grant in context['granted_inputs'].values():
        require(hashlib.sha256(grant['utf8'].encode()).hexdigest() == grant['sha256'], 'invalid corpus contract')
        require(len(grant['utf8'].encode()) <= context['budgets']['input_bytes'], 'invalid corpus contract')
    accounts = set(context['budgets']) | {'granted_inputs', 'request_id',
                                        'generation', 'cancellation', 'publication'}
    require({r['attack'] for r in data['cases']} == AUTHORITY | PUBLICATION | {
        'input', 'spin', 'silent-spin', 'stdout', 'stderr', 'combined', 'exact',
        'cancel-before-start', 'cancel-running'}, 'invalid corpus contract')
    for row in data['cases']:
        require(row['C_accounts'] and set(row['C_accounts']) <= accounts, 'invalid corpus contract')
        require(row['granted_inputs'] == ['source'], 'invalid corpus contract')
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
                published_sha256=hashlib.sha256(payload).hexdigest(), reaped=None, events=events)


class AuthorityObserver:
    """Linux test instruments owned by the harness, not worker status strings."""
    def __init__(self, folder):
        self.secret = folder / 'private-fixture'
        self.canary = os.urandom(24).hex().encode()
        self.secret.write_bytes(self.canary)
        self.before = hashlib.sha256(self.canary).hexdigest()
        self.listener = socket.socket()
        self.listener.bind(('127.0.0.1', 0))
        self.listener.listen(4)
        self.listener.setblocking(False)
        self.fd = os.open(self.secret, os.O_RDONLY)
        require(Path('/proc/self/task').is_dir(), 'Linux process observer unavailable')
        libc = ctypes.CDLL(None, use_errno=True)
        # A subreaper lets this test supervisor wait for orphaned group members.
        require(libc.prctl(36, 1, 0, 0, 0) == 0, 'Linux child subreaper unavailable')
        self.watch = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        require(self.watch >= 0, 'Linux filesystem observer unavailable')
        require(libc.inotify_add_watch(self.watch, os.fsencode(self.secret), 1) >= 0,
                'cannot observe fixture reads')  # IN_ACCESS
        self.connections = 0
        self.children = set()

    def sample(self, process):
        while True:
            try:
                connection, _ = self.listener.accept()
                self.connections += 1
                connection.close()
            except BlockingIOError:
                break
        children = Path(f'/proc/{process.pid}/task/{process.pid}/children')
        try:
            self.children.update(map(int, children.read_text().split()))
        except FileNotFoundError:
            pass

    def finish(self, captured, reaped_children):
        reads = 0
        while True:
            try:
                events = os.read(self.watch, 8192)
            except BlockingIOError:
                break
            offset = 0
            while offset < len(events):
                _, mask, _, size = struct.unpack_from('iIII', events, offset)
                reads += bool(mask & 1)
                offset += 16 + size
        # Read the watch before hashing; harness reads must not become attacks.
        after = hashlib.sha256(self.secret.read_bytes()).hexdigest()
        return dict(fixture_reads=reads, fixture_sha256_before=self.before,
                    fixture_sha256_after=after, listener_accepts=self.connections,
                    descendant_pids=sorted(self.children | set(reaped_children)),
                    descriptor_offset=os.lseek(self.fd, 0, os.SEEK_CUR),
                    environment_canary_echoed=self.canary in captured['stdout'])

    def close(self):
        self.listener.close()
        os.close(self.fd)
        os.close(self.watch)


def authority_escaped(attack, evidence):
    return {
        'filesystem-read': evidence['fixture_reads'] > 0,
        'filesystem-write': evidence['fixture_sha256_before'] != evidence['fixture_sha256_after'],
        'environment': evidence['environment_canary_echoed'],
        'network': evidence['listener_accepts'] > 0,
        'process': bool(evidence['descendant_pids']),
        'inherited-descriptor': evidence['descriptor_offset'] > 0,
    }[attack]


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=2)
    children = []
    deadline = time.monotonic() + 2
    while True:
        try:
            pid, _ = os.waitpid(-process.pid, os.WNOHANG)
        except ChildProcessError:
            break
        if pid:
            children.append(pid)
        elif time.monotonic() < deadline:
            time.sleep(.005)
        else:
            break
    try:
        os.killpg(process.pid, 0)
        empty = False
    except ProcessLookupError:
        empty = True
    return dict(reaped=process.returncode is not None, group_empty=empty,
                reaped_descendants=children)


def execute(context, attack, profile, folder, worker_mode='honest'):
    permissive = profile == 'permissive'
    if profile == 'native-unavailable':
        return dict(status='isolation-unavailable', published_bytes=0,
                    launched=False, reaped=None)
    if attack in PUBLICATION:
        return publication_case(context, attack, permissive)
    if attack == 'cancel-before-start' and not permissive:
        return dict(status='cancelled', published_bytes=0, launched=False, reaped=None)
    if attack == 'cancel-before-start':
        attack = 'input'
    observer = AuthorityObserver(folder)
    process = None
    budget = context['budgets']
    captured = {'stdout': bytearray(), 'stderr': bytearray()}
    started = time.monotonic()
    status = None
    try:
        path = observer.secret
        env = dict(os.environ, CONFINEMENT_DISPOSABLE_ENV=observer.canary.decode())
        if worker_mode == 'denied':
            # Real absent authority, including workers exiting nonzero on denial.
            path = folder / 'absent-fixture'
            env.pop('CONFINEMENT_DISPOSABLE_ENV', None)
        command = [sys.executable, str(WORKER), attack, profile, str(path),
                   str(observer.listener.getsockname()[1]), str(observer.fd), worker_mode]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True,
                                   pass_fds=(observer.fd,), env=env)
        process.stdin.write(context['granted_inputs']['source']['utf8'].encode())
        process.stdin.close()
        with selectors.DefaultSelector() as selector:
            for name in captured:
                stream = getattr(process, name)
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            # A worker can close both pipes and keep computing.
            while selector.get_map() or process.poll() is None:
                observer.sample(process)
                elapsed = time.monotonic() - started
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
            status = 'worker-failed' if process.wait(timeout=1) else 'complete'
    finally:
        try:
            if process:
                observer.sample(process)
                cleanup = stop_group(process)
                process.stdout.close()
                process.stderr.close()
            evidence = observer.finish(captured, cleanup['reaped_descendants'] if process else [])
        finally:
            observer.close()
    if attack in AUTHORITY:
        # Escape evidence overrides any worker claim or exit status. A completed
        # denied attempt may exit nonzero; a deadline/crash is not proof of denial.
        if authority_escaped(attack, evidence):
            status = 'authority-escaped'
        elif status in {'complete', 'worker-failed'} and process.returncode >= 0:
            status = 'authority-denied'
    for name, payload in captured.items():
        (folder / (name + '.bin')).write_bytes(payload)
    payload = captured['stdout'] if status == 'complete' else b''
    return dict(status=status, published_bytes=len(payload),
                published_sha256=hashlib.sha256(payload).hexdigest(),
                captured_bytes=sum(map(len, captured.values())), launched=True,
                worker_exit=process.returncode, authority=evidence, **cleanup,
                elapsed_ms=round((time.monotonic()-started)*1000))


def run(data, profile, output):
    output.mkdir(parents=True)
    rows = []
    for case in data['cases']:
        folder = output / case['id']
        folder.mkdir()
        observation = execute(data['C'], case['attack'], profile, folder)
        expected_bytes = case.get('expected_bytes', 0)
        passed = (observation['status'] == case['expected']
                  and observation['published_bytes'] == expected_bytes
                  and (not observation['launched'] or
                       (observation['reaped'] and observation['group_empty'])))
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
        require(result.returncode == 1, f'{profile} must fail the command-line corpus')
        receipts = list(destination.glob('worker-corpus-*/' + profile + '/receipt.json'))
        require(len(receipts) == 1, 'invalid corpus contract')
        negatives.append(json.loads(receipts[0].read_text()))
    permissive, unavailable = negatives
    require(model['passed'], 'reference contract model failed')
    failures = {r['id'] for r in permissive['rows'] if not r['passed']}
    # Mutation control: each unsafe policy change must be detected, including
    # each authority probe, both cancellation points and each stale identity.
    require(failures == {r['id'] for r in data['cases']} - {
        'granted-input', 'exact-output', 'current-response'}, 'invalid corpus contract')
    require(not permissive['passed'], 'invalid corpus contract')
    require(not unavailable['passed'] and unavailable['admission'] == 'isolation-unavailable', 'invalid corpus contract')
    require(all(not r['observed']['launched'] and r['observed']['status'] == 'isolation-unavailable'
               for r in unavailable['rows']), 'invalid corpus contract')
    require(all(not r['production_admission'] and not r['qualification']
               and not r['trusted_native_fallback'] for r in [model, permissive, unavailable]), 'invalid corpus contract')
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
        require((ROOT / 'docs/WORKER_CORPUS.md').is_file(), 'invalid corpus contract')
        print('PASS 20 case mappings; test-only context, no production admission')
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
