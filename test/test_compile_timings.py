#!/usr/bin/env python3
"""Small phase-presence and byte-equality contract, using COMPILER."""
import importlib.util
import json
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
    def test_json_diagnostics_rejects_timings(self):
        compiler = str((ROOT / os.environ.get('COMPILER', 'out/lang_next')).resolve())
        env = dict(os.environ, LANGBE='llvm')
        with tempfile.TemporaryDirectory(prefix='test-json-timings-') as directory:
            output = Path(directory) / 'program.ll'
            for flags in (['--timings', '--diagnostics=json'],
                          ['--diagnostics=json', '--timings']):
                with self.subTest(flags=flags):
                    command = [compiler, 'compile', 'test/timings/main.lang',
                               *flags, '-o', str(output)]
                    result = subprocess.run(command, cwd=ROOT, env=env,
                                            capture_output=True, text=True, timeout=15)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, '')
                    self.assertFalse(output.exists())
                    records = [json.loads(line) for line in result.stderr.splitlines()]
                    self.assertEqual(len(records), 1)
                    self.assertEqual(records[0]['version'], 1)
                    self.assertEqual(records[0]['code'], 'unsupported-mode')
                    self.assertEqual(records[0]['severity'], 'error')
                    self.assertIn('--timings cannot be combined with --diagnostics=json',
                                  records[0]['message'])
                    print(result.stderr, end='')

    def check_output(self, command, output, env):
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
            self.assertGreaterEqual(row['cpu_ms'], 0)
        self.assertEqual(rows['output']['count'], len(expected))
        print(f'{command[2:]}: identical output ({len(expected)} bytes)')
        print(timed.stderr, end='')
        return rows

    def test_ast_paths(self):
        compiler = str((ROOT / os.environ.get('COMPILER', 'out/lang_next')).resolve())
        env = dict(os.environ, LANGBE='llvm')
        with tempfile.TemporaryDirectory(prefix='test-ast-timings-') as directory:
            for mode in ('--emit-ast', '--emit-expanded-ast', '--emit-exe-ast'):
                with self.subTest(mode=mode):
                    output = Path(directory) / f'{mode}.ast'
                    command = [compiler, 'compile', 'test/timings/main.lang', mode,
                               '-o', str(output)]
                    rows = self.check_output(command, output, env)
                    self.assertGreater(rows['parsing']['count'], 0)
                    self.assertGreater(rows['type-checking-lowering-ir-emission']['count'], 0)
                    if mode != '--emit-ast':
                        self.assertGreater(rows['expansion-registration']['count'], 0)

            # The expanded fixture has two user functions plus module metadata.
            # Exercise both plain AST parsing and the reader source-context path.
            ast_input = Path(directory) / '--emit-expanded-ast.ast'
            for context in ([], ['--ast-source', 'test/timings/main.lang']):
                for mode in ([], ['--emit-ast']):
                    with self.subTest(context=context, mode=mode):
                        target = Path(directory) / 'from-ast'
                        command = [compiler, 'compile', '--from-ast', str(ast_input),
                                   *context, *mode, '-o', str(target)]
                        rows = self.check_output(command, target, env)
                        self.assertEqual(rows['parsing']['count'], 3)
                        self.assertGreater(rows['parsing']['cpu_ms'], 0)
                        self.assertGreater(rows['type-checking-lowering-ir-emission']['count'], 0)

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
