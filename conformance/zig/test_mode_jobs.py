#!/usr/bin/env python3
"""Exercise actual orphan, cancellation and resource cleanup with hostile trees."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from mode_jobs import supervise

SCRIPT = r'''import os, subprocess, sys, time
from pathlib import Path
kind, marker = sys.argv[1:]
if kind == 'affinity':
    Path(marker).write_text(str(len(os.sched_getaffinity(0))))
    time.sleep(.15)
else:
    code = "import os,time; os.setsid(); time.sleep(60)"
    if kind == 'forkchain':
        code = "import os,time\nfor _ in range(12):\n if os.fork(): break\n time.sleep(.002)\ntime.sleep(60)"
    child = subprocess.Popen([sys.executable, '-c', code])
    Path(marker).write_text(str(child.pid))
    if kind == 'orphan': os._exit(0)
    if kind == 'memory': data = bytearray(300 * 1024 * 1024)
    if kind == 'processes':
        children = [subprocess.Popen([sys.executable, '-c', code]) for _ in range(10)]
    time.sleep(60)
'''


class SupervisionTests(unittest.TestCase):
    def job(self, kind):
        folder = Path(tempfile.mkdtemp(prefix=kind + '-', dir=OUTPUT))
        marker = folder / 'pid'
        command = [sys.executable, '-c', SCRIPT, kind, str(marker)]
        return folder, marker, [('debug', command)]

    def run_job(self, folder, commands, **changes):
        options = dict(memory_mib=512, cpus=2, processes=32, timeout=5)
        options.update(changes)
        return supervise(commands, 1, folder, **options)

    def gone(self, marker):
        self.assertTrue(marker.exists())
        self.assertFalse(Path('/proc', marker.read_text()).exists())

    def test_inherited_affinity(self):
        folder, marker, commands = self.job('affinity')
        before = os.sched_getaffinity(0)
        result = self.run_job(folder, commands)
        self.assertEqual(int(marker.read_text()), min(2, len(before)))
        self.assertEqual(os.sched_getaffinity(0), before)
        self.assertEqual(result['remaining_descendants'], [])

    def test_bounded_overlap(self):
        folder, marker, commands = self.job('affinity')
        command = commands[0][1]
        result = supervise([(mode, command) for mode in ('debug', 'safe', 'fast')], 2, folder,
                           memory_mib=512, cpus=2, processes=32, timeout=5)
        modes = result['modes']
        self.assertEqual(result['max_running_modes'], 2)
        self.assertLess(modes['safe']['started_seconds'], modes['debug']['finished_seconds'])
        self.assertGreaterEqual(modes['fast']['started_seconds'],
                                min(modes[m]['finished_seconds'] for m in ('debug', 'safe')))
        self.assertEqual(result['remaining_descendants'], [])

    def test_orphan_with_new_session(self):
        folder, marker, commands = self.job('orphan')
        self.run_job(folder, commands)
        self.gone(marker)

    def test_fork_chain_cleanup(self):
        folder, marker, commands = self.job('forkchain')
        with self.assertRaises(TimeoutError):
            self.run_job(folder, commands, timeout=.1)
        self.gone(marker)
        self.assertEqual(json.loads((folder / 'resources.json').read_text())['remaining_descendants'], [])

    def test_failure_cancels_sibling(self):
        folder, marker, commands = self.job('cancel')
        commands.append(('safe', [sys.executable, '-c', 'import time; time.sleep(.15); exit(3)']))
        with self.assertRaisesRegex(RuntimeError, 'worker failed'):
            supervise(commands, 2, folder, memory_mib=512, cpus=2, processes=32, timeout=5)
        self.gone(marker)
        self.assertEqual(json.loads((folder / 'resources.json').read_text())['remaining_descendants'], [])

    def test_affinity_escape(self):
        before = os.sched_getaffinity(0)
        if len(before) < 3:
            self.skipTest('affinity escape needs three available CPUs')
        folder, marker, _ = self.job('affinity-escape')
        command = [sys.executable, '-c', 'import os,time; os.sched_setaffinity(0, ' + repr(before) + '); time.sleep(60)']
        with self.assertRaisesRegex(RuntimeError, 'affinity limit'):
            self.run_job(folder, [('debug', command)])

    def test_timeout_tree(self):
        folder, marker, commands = self.job('timeout')
        with self.assertRaises(TimeoutError):
            self.run_job(folder, commands, timeout=.4)
        self.gone(marker)

    def test_aggregate_memory(self):
        folder, marker, commands = self.job('memory')
        with self.assertRaisesRegex(RuntimeError, 'RSS limit'):
            self.run_job(folder, commands, memory_mib=256)
        self.gone(marker)

    def test_aggregate_processes(self):
        folder, marker, commands = self.job('processes')
        with self.assertRaisesRegex(RuntimeError, 'process limit'):
            self.run_job(folder, commands, processes=4)
        self.gone(marker)

    def test_cancellation_tree(self):
        self.cancellation(False)

    def test_repeated_cancellation_during_cleanup(self):
        self.cancellation(True)

    def cancellation(self, repeated):
        folder, marker, commands = self.job('cancel')
        cleanup_marker = folder / 'cleaning'
        prefix = 'import sys; from pathlib import Path; from mode_jobs import supervise; '
        if repeated:
            prefix = ('import time, mode_jobs; from pathlib import Path; '
                      'original = mode_jobs.cleanup; '
                      'mode_jobs.cleanup = lambda processes: (Path(' + repr(str(cleanup_marker)) + ').write_text("1"), '
                      'time.sleep(.3), original(processes))[-1]; supervise = mode_jobs.supervise; ')
        code = (prefix +
                'supervise(' + repr(commands) + ', 1, Path(' + repr(str(folder)) + '), '
                'memory_mib=512, cpus=2, processes=32, timeout=60)')
        with (folder / 'cancel.log').open('w') as log:
            process = subprocess.Popen([sys.executable, '-B', '-c', code],
                                       cwd=Path(__file__).resolve().parent, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 10
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(marker.exists())
                process.send_signal(signal.SIGTERM)
                if repeated:
                    deadline = time.monotonic() + 5
                    while not cleanup_marker.exists() and time.monotonic() < deadline:
                        time.sleep(.005)
                    self.assertTrue(cleanup_marker.exists())
                    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
                        process.send_signal(sig)
                        time.sleep(.01)
                self.assertNotEqual(process.wait(timeout=10), 0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
        self.gone(marker)
        report = json.loads((folder / 'resources.json').read_text())
        self.assertEqual(report['remaining_descendants'], [])
        self.assertIn('cancelled', report['error'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    OUTPUT = args.work.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    unittest.main(argv=[sys.argv[0], *remaining])
