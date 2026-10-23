#!/usr/bin/env python3
"""Disposable attack worker for the contract corpus, never a production reader."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def main():
    attack, profile, path, port, descriptor, mode = sys.argv[1:]
    if attack in {'filesystem-read', 'filesystem-write', 'environment', 'network',
                  'process', 'inherited-descriptor'}:
        # This cooperative branch models an authority broker. It is NOT an OS
        # boundary: an arbitrary native program could simply bypass this branch.
        if profile == 'policy-model' and mode == 'honest':
            return
        if attack == 'filesystem-read':
            Path(path).read_bytes()
        elif attack == 'filesystem-write':
            Path(path).write_bytes(b'changed')
        elif attack == 'environment':
            sys.stdout.buffer.write(os.environ['CONFINEMENT_DISPOSABLE_ENV'].encode())
            sys.stdout.buffer.flush()
        elif attack == 'network':
            with socket.create_connection(('127.0.0.1', int(port)), timeout=1):
                pass
        elif attack == 'process':
            # Keep the child observable until supervisor cleanup, then leave it
            # orphaned to exercise descendant reaping as well as group killing.
            subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.read(int(descriptor), 1)
        print('authority-denied' if mode == 'lie' else 'authority-escaped')
    elif attack == 'input':
        sys.stdout.buffer.write(sys.stdin.buffer.read())
    elif attack == 'exact':
        sys.stdout.buffer.write(b'x' * 1024)
    elif attack in {'stdout', 'stderr', 'combined'}:
        if attack == 'combined':
            os.write(1, b'x' * 600)
            os.write(2, b'x' * 600)
        else:
            os.write(1 if attack == 'stdout' else 2, b'x' * 1025)
    elif attack == 'cancel-running':
        # A pipe handshake makes cancellation happen after worker execution,
        # without depending on a sleep or a scheduling race.
        os.write(2, b'READY\n')
        while True:
            pass
    elif attack in {'spin', 'silent-spin'}:
        if attack == 'silent-spin':
            os.close(1)
            os.close(2)
        while True:
            pass
    else:
        print(json.dumps({'unexpected-attack': attack}))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
