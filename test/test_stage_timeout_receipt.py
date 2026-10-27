#!/usr/bin/env python3
"""Exercise the real process group and retained diagnostics on deadline."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from stage_host import Host, StageError
from stage_protocol import MAX_BYTES


class TimeoutReceipt(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.host = Host(sys.executable, self.directory, controlled_fixtures=True)
        self.host.worker_timeout = 1

    def worker(self):
        script = '''import os, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
open('child.pid', 'w').write(str(child.pid))
os.write(1, b'O' * %d)
os.write(2, b'E' * %d)
while True: time.sleep(1)
''' % (MAX_BYTES + 100, MAX_BYTES + 100)
        return [sys.executable, '-c', script]

    def run_timeout(self, fail_receipt=False):
        processes = []
        real_popen = subprocess.Popen
        def capture(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            processes.append(process)
            return process
        real_write = Path.write_text
        def write(path, *args, **kwargs):
            if fail_receipt and path.name == 'process-1.json':
                raise OSError('receipt unavailable')
            return real_write(path, *args, **kwargs)
        argv = self.worker()
        with mock.patch('stage_host.subprocess.Popen', side_effect=capture), mock.patch.object(Path, 'write_text', write):
            with self.assertRaises(StageError) as error:
                self.host.run(argv, self.directory)
        self.assertEqual(str(error.exception), 'worker-deadline')
        process = processes[0]
        self.assertEqual(process.returncode, -signal.SIGKILL)
        with self.assertRaises(ChildProcessError):
            os.waitpid(process.pid, os.WNOHANG)
        child = int((self.directory / 'child.pid').read_text())
        # An orphan may briefly remain as a zombie until its adopter reaps it.
        for _ in range(100):
            try:
                stat = Path('/proc') / str(child) / 'stat'
                state = stat.read_text().split(') ', 1)[1][0] if stat.exists() else None
                if state in (None, 'Z'): break
            except FileNotFoundError:
                break
            time.sleep(.01)
        else: self.fail('child still running after process-group cleanup')
        self.assertEqual((self.directory / 'process-1.stdout').read_bytes(), b'O' * (MAX_BYTES + 17))
        self.assertEqual((self.directory / 'process-1.stderr').read_bytes(), b'E' * MAX_BYTES)
        if not fail_receipt:
            receipt = json.loads((self.directory / 'process-1.json').read_text())
            self.assertEqual(receipt, {'argv': argv, 'exit': -signal.SIGKILL, 'timed_out': True})

    def test_timeout_retains_receipt_and_reaps_group(self):
        self.run_timeout()

    def test_receipt_failure_keeps_timeout_primary(self):
        self.run_timeout(fail_receipt=True)

    def test_completed_workers_preserve_behavior(self):
        self.assertEqual(self.host.run([sys.executable, '-c', "import sys; print('ok'); print('note', file=sys.stderr)"], self.directory), b'ok\n')
        self.assertEqual(json.loads((self.directory / 'process-1.json').read_text())['exit'], 0)
        with self.assertRaisesRegex(StageError, 'worker-failed: bad'):
            self.host.run([sys.executable, '-c', "import sys; print('bad', file=sys.stderr); sys.exit(7)"], self.directory)
        self.assertEqual(json.loads((self.directory / 'process-2.json').read_text())['exit'], 7)
        with self.assertRaisesRegex(StageError, 'worker-output-limit'):
            self.host.run([sys.executable, '-c', 'import os; os.write(1, b"x" * %d)' % (MAX_BYTES + 17)], self.directory)
        with self.assertRaisesRegex(StageError, 'native-confinement-unavailable'):
            Host(sys.executable, self.directory)
        self.assertEqual(Host.worker_timeout, 90)


if __name__ == '__main__':
    unittest.main()
