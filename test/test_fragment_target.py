#!/usr/bin/env python3
"""Four focused regressions for fragment command lifetime and results."""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fragment', ROOT / 'scripts/fragment.py')
fragment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fragment)


class FragmentTargetTests(unittest.TestCase):
    def test_success_preserves_output(self):
        result = fragment.invoke([sys.executable, '-c',
                                  'import sys; print("out"); print("err", file=sys.stderr)'],
                                 os.environ)
        self.assertEqual(result, (0, 'out\nerr\n'))

    def test_failure_preserves_status(self):
        result = fragment.invoke([sys.executable, '-c', 'raise SystemExit(7)'], os.environ)
        self.assertEqual(result, (7, ''))

    def timeout_reader(self, close_pipes):
        # The reader ignores TERM and has no output dependency on its parent.
        # A delayed marker also checks liveness portably without relying on /proc.
        with tempfile.TemporaryDirectory(prefix='fragment-regression-') as tmp:
            pidfile, marker = Path(tmp) / 'pid', Path(tmp) / 'survived'
            reader = ('import os,signal,time; from pathlib import Path; '
                      'signal.signal(signal.SIGTERM, signal.SIG_IGN); '
                      f'Path({str(pidfile)!r}).write_text(str(os.getpid())); '
                      'time.sleep(1.5); '
                      f'Path({str(marker)!r}).write_text("survived")')
            compiler = ('import subprocess,sys,time; '
                        f'subprocess.Popen([sys.executable,"-c",{reader!r}]'
                        + (', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)' if close_pipes else ')')
                        + ('; time.sleep(60)' if close_pipes else ''))
            try:
                start = time.monotonic()
                with self.assertRaises(subprocess.TimeoutExpired):
                    fragment.invoke([sys.executable, '-c', compiler], os.environ, timeout=1)
                self.assertLess(time.monotonic() - start, 3)
                self.assertTrue(pidfile.is_file(), 'reader must have started before timeout')
                time.sleep(1)
                self.assertFalse(marker.exists(), 'reader survived command timeout')
            finally:
                if pidfile.exists():
                    try:
                        os.kill(int(pidfile.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_timeout_kills_reader_with_inherited_pipes(self):
        self.timeout_reader(close_pipes=False)

    def test_timeout_kills_reader_with_closed_pipes(self):
        self.timeout_reader(close_pipes=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
