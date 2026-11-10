#!/usr/bin/env python3
"""Exercise site archive validation before deployment can contact a server."""
import hashlib
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / 'web/verify_archive.py'
# Mirror the shipped archive inventory so omissions are exercised independently.
FILES = '''build_stdlib.js compiler-receipt.json compiler.wasm compiler_host.js editor.js
examples/fib.lang examples/fib.wasm examples/mandelbrot.lang examples/mandelbrot.wasm
examples/polyglot_wasm.lang examples/polyglot_wasm.wasm host.js index.html lab.html
program_host.js readers.html receipt.json stdlib.json'''.split()


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive(self, names, contents=None):
        path = self.root / 'site.tar.gz'
        with tarfile.open(path, 'w:gz') as tar:
            manifest = []
            for name in names:
                data = (contents or {}).get(name, name.encode())
                item = tarfile.TarInfo(name)
                item.size = len(data)
                tar.addfile(item, io.BytesIO(data))
                manifest.append(f'{hashlib.sha256(data).hexdigest()}  {name}\n')
            data = ''.join(manifest).encode()
            item = tarfile.TarInfo('MANIFEST')
            item.size = len(data)
            tar.addfile(item, io.BytesIO(data))
        return path

    def verify(self, names):
        return subprocess.run(['python3', str(VERIFIER), str(self.archive(names)),
                               str(self.root / 'output')], capture_output=True)

    def test_complete_inventory(self):
        self.assertEqual(self.verify(FILES).returncode, 0)

    def test_each_missing_asset_is_rejected(self):
        for name in FILES:
            with self.subTest(name=name):
                self.assertNotEqual(self.verify([f for f in FILES if f != name]).returncode, 0)

    def test_current_directory_alias_is_rejected(self):
        for name in ('./index.html', 'examples/./fib.lang'):
            with self.subTest(name=name):
                self.assertNotEqual(self.verify(FILES + [name]).returncode, 0)

    def test_incomplete_deploy_never_calls_ssh_or_scp(self):
        archive = self.archive(['index.html'])
        marker = self.root / 'contacted'
        for command in ('ssh', 'scp'):
            stub = self.root / command
            stub.write_text(f'#!/bin/sh\ntouch "{marker}"\n')
            stub.chmod(0o755)
        env = dict(os.environ, PATH=f'{self.root}:{os.environ["PATH"]}')
        result = subprocess.run(['bash', str(ROOT / 'web/deploy.sh'), 'ship', str(archive)],
                                env=env, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
