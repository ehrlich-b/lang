#!/usr/bin/env python3
"""Byte compatibility and worker routing tests without a compiler build."""
import glob
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from suite_manifest import classify


class ManifestTests(unittest.TestCase):
    def compare(self, paths):
        old = subprocess.check_output(['bash', 'test/suite_metadata_reference.sh', *paths])
        new = subprocess.check_output(['python3', 'test/suite_manifest.py', *paths])
        self.assertEqual(old, new)
        return new

    def test_retained_suite(self):
        paths = sorted(glob.glob('test/suite/*.lang'))
        self.assertTrue(paths)
        self.compare(paths)
        print(f'Compared all classification bytes for {len(paths)} retained files')

    def test_header_edges(self):
        cases = [
            (b'// expect: 42', (b'', b'42', b'')),
            (b'// reject: i128 needs 64 bits', (b'r', b'128\n64', b'i128 needs 64 bits')),
            (b'// expect: 007 and 42\n', (b'', b'007\n42', b'')),
            (b'// unknown\nfunc main() i64 { return 0; }', (b'', b'', b'')),
            (b'//ignore // expect: 1\n//linux\n//macos //clang\n', (b'ilmc', b'1', b'')),
            (b'// expect: 0\n\n\n//ignore //linux //macos //clang\n', (b'', b'0', b'')),
            (b'// reject: digit 2\r\n', (b'r', b'2', b'digit 2\r')),
            (b'', (b'', b'', b'')),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for n, (content, expected) in enumerate(cases):
                path = str(Path(tmp) / f'header {n}.lang')
                Path(path).write_bytes(content)
                self.assertEqual(classify(path)[1:], expected)
                paths.append(path)
            self.compare(paths)

    def test_missing_input_fails_batch(self):
        result = subprocess.run(['python3', 'test/suite_manifest.py',
                                 'test/suite/001_return_0.lang', 'missing.lang'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'')

    def test_worker_routes_and_fragment(self):
        # Tool doubles isolate routing and assertion behavior; real compiler
        # fragment checks are run separately with the same production runner.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for tool, body in {
                'compiler': 'case "$1" in *reject*) echo "i128 needs 64 bits"; exit 1;; esac\nexit 0',
                'lli': 'if [ "$1" = --help ]; then echo jit-kind; fi\nexit 42',
                'clang': 'while [ "$1" != -o ]; do shift; done\nshift\nprintf "#!/bin/sh\\nexit 42\\n" > "$1"\nchmod +x "$1"',
            }.items():
                path = root / tool
                path.write_text('#!/bin/bash\n' + body + '\n')
                path.chmod(0o755)
            files = {
                'lli': '// expect: 42',
                'native': '// expect: 42\n//clang',
                'reject': '// reject: i128 needs 64 bits',
                'ignored': '//ignore\n// reject: wrong',
                'platform': '// expect: 42\n//macos',
                'both': '// expect: 42\n//linux\n//macos',
            }
            paths = []
            for name, header in files.items():
                path = root / (name + '.lang')
                path.write_text(header)
                paths.append(str(path))
            env = dict(os.environ, PATH=str(root) + ':' + os.environ['PATH'],
                       COMPILER=str(root / 'compiler'), LANGOS='linux')
            for jobs in ('1', '2'):
                result = subprocess.run(['bash', 'test/run_llvm_suite.sh', *paths],
                                        env=dict(env, JOBS=jobs), capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('Passed: 3 / 3', result.stdout)
                self.assertIn('Skipped: 3', result.stdout)
                self.assertNotIn('reader_', result.stdout)
            for header in ('// unknown', '// expect: 4 and 2', '// expect: 042'):
                path = root / 'unknown.lang'
                path.write_text(header)
                result = subprocess.run(['bash', 'test/run_llvm_suite.sh', str(path)],
                                        env=dict(env, JOBS='2'), capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('FAIL unknown', result.stdout)


if __name__ == '__main__':
    unittest.main()
