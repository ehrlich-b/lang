#!/usr/bin/env python3
"""Independent STG1 inputs checked against both copied-value decoders."""
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
from stage_host import Host
from stage_protocol import Value, WireError, frame, unframe


def value(tag, payload=b''):
    return bytes([tag]) + struct.pack('<I', len(payload)) + payload


def text(s):
    return value(7, s.encode('utf-8'))


def container(tag, entries):
    return value(tag, struct.pack('<I', len(entries)) + b''.join(entries))


def record(tag, pairs):
    return container(tag, [text(k) + v for k, v in pairs])


def raw_frame(payload):
    return b'STG1' + struct.pack('<III', len(payload), 1, 0) + payload


class DuplicateKeys(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='duplicate-keys-')
        compiler = Path(os.environ.get('COMPILER', 'out/lang')).resolve()
        host = Host(compiler, Path(cls.temp.name) / 'workers', controlled_fixtures=True)
        spec = host.fixtures['echo']
        target = Value('descriptor', {'backend': Value('text', 'llvm'),
                                    'target': Value('text', 'wasm32'),
                                    'pointer_bits': Value('i64', 32)})
        token = host.compile('echo', spec['params'], spec['result'], target)
        cls.worker = host.artifacts[token].path

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def compare(self, payload, accepted):
        raw = raw_frame(container(8, [payload]))
        proc = subprocess.run([self.worker], input=raw, capture_output=True, timeout=10)
        if accepted:
            expected = unframe(raw, 1)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(unframe(proc.stdout, 2), expected.data[0])
            self.assertEqual(proc.stderr, b'')
        else:
            with self.assertRaisesRegex(WireError, '^record-key$'):
                unframe(raw, 1)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, b'')
            self.assertIn(b'stage-error: record-key', proc.stderr)

    def test_duplicate_record_keys(self):
        for key in ('a', 'é', 'e\u0301', '🦋'):
            with self.subTest(key=key):
                self.compare(record(9, [(key, value(0)), (key, value(1, b'\x01'))]), False)

    def test_duplicate_descriptor_keys(self):
        for key in ('', '漢', 'é'):
            with self.subTest(key=key):
                self.compare(record(11, [(key, value(0)), (key, value(0))]), False)

    def test_nested_duplicate_keys(self):
        for outer, inner in ((9, 11), (11, 9)):
            with self.subTest(outer=outer, inner=inner):
                bad = record(inner, [('x', value(0)), ('x', value(0))])
                self.compare(record(outer, [('nested', bad)]), False)

    def test_valid_distinct_nested_keys_and_sorted_encoding(self):
        inner = record(11, [('e\u0301', value(0)), ('é', value(1, b'\x01'))])
        payload = record(9, [('a', inner), ('🦋', value(0))])
        self.compare(payload, True)
        expected = Value('record', {'🦋': Value('null'), 'a': Value('descriptor', {
            'é': Value('bool', True), 'e\u0301': Value('null')})})
        self.assertEqual(frame(expected)[16:], payload)


if __name__ == '__main__':
    unittest.main()
