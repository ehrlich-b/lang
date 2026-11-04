#!/usr/bin/env python3
"""Small phase-presence and byte-equality contract, using COMPILER."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('phases', ROOT / 'benchmark/compile/phases.py')
phases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phases)


class CompileTimingsTest(unittest.TestCase):
    def test_phases_and_unchanged_output(self):
        compiler = str((ROOT / os.environ.get('COMPILER', 'out/lang_next')).resolve())
        # Respect TMPDIR so callers can retain all evidence outside the checkout.
        with tempfile.TemporaryDirectory(prefix='test-compile-timings-') as directory:
            for backend in ('llvm', 'x86', 'wasm'):
                with self.subTest(backend=backend):
                    env = dict(os.environ, LANGBE=backend)
                    output = Path(directory) / 'program'
                    command = [compiler, 'compile', 'test/timings/main.lang', '-o', str(output)]
                    plain = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                           text=True, timeout=15, check=True)
                    expected = output.read_bytes()
                    timed = subprocess.run(command + ['--timings'], cwd=ROOT, env=env,
                                           capture_output=True, text=True, timeout=15, check=True)
                    rows = phases.parse_timings(timed.stderr)
                    self.assertEqual(plain.stderr, '')
                    self.assertEqual(timed.stdout, plain.stdout)
                    self.assertEqual(output.read_bytes(), expected)
                    for row in rows.values():
                        self.assertGreater(row['count'], 0)
                        self.assertGreaterEqual(row['cpu_ms'], 0)
                    self.assertGreater(rows['tokens']['count'], 20)  # Included source too.
                    if backend != 'x86':  # x86 streams its data section separately.
                        self.assertEqual(rows['output']['count'], len(expected))
                    print(f'{backend}: all phases, included source, identical output ({len(expected)} bytes)')
                    print(timed.stderr, end='')


if __name__ == '__main__':
    unittest.main()
