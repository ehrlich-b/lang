#!/usr/bin/env python3
"""Direct encoder contract tests; no worker processes are involved."""
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
import stage_protocol as wire

V = wire.Value


class UnicodeWireTests(unittest.TestCase):
    def test_surrogates_rejected_with_cause(self):
        for bad in ('\ud800', '\udc00', '\ud800\udc00'):
            for value in (V('text', bad), V('syntax', '(program ' + bad + ')'),
                          V('record', {bad: V('null')}),
                          V('descriptor', {bad: V('null')})):
                with self.subTest(bad=ascii(bad), kind=value.kind):
                    with self.assertRaisesRegex(wire.WireError, '^invalid-utf8$') as caught:
                        wire.encode(value)
                    self.assertIsInstance(caught.exception.__cause__, UnicodeEncodeError)

    def test_valid_text_bytes_and_roundtrip(self):
        for text in ('🦋', 'e\u0301', 'é'):
            for kind, content in (('text', text), ('syntax', '(program ' + text + ')')):
                with self.subTest(kind=kind, text=text):
                    raw = content.encode('utf-8')
                    encoded = bytes([wire.TAGS[kind]]) + struct.pack('<I', len(raw)) + raw
                    self.assertEqual(wire.encode(V(kind, content)), encoded)
                    self.assertEqual(wire.decode(encoded), V(kind, content))
            for kind in ('record', 'descriptor'):
                value = V(kind, {text: V('text', text)})
                encoded = wire.encode(value)
                self.assertEqual(wire.decode(encoded), value)
                self.assertEqual(wire.encode(wire.decode(encoded)), encoded)
                self.assertEqual(encoded.count(text.encode('utf-8')), 2)

    def test_existing_validation_and_budgets(self):
        cycle = V('list', [])
        cycle.data.append(cycle)
        for value, message in ((V('text', 1), 'text-value'),
                               (V('syntax', 'bad'), 'syntax-value'),
                               (V('record', {1: V('null')}), 'record-value'),
                               (V('list', [object()]), 'non-wire-value'),
                               (cycle, 'cyclic-wire-object')):
            with self.subTest(message=message), self.assertRaisesRegex(wire.WireError, '^' + message + '$'):
                wire.encode(value)
        with patch.object(wire, 'MAX_DEPTH', 0), self.assertRaisesRegex(wire.WireError, '^wire-budget$'):
            wire.encode(V('list', [V('null')]))
        with patch.object(wire, 'MAX_ITEMS', 1), self.assertRaisesRegex(wire.WireError, '^wire-budget$'):
            wire.encode(V('list', [V('null')]))
        with patch.object(wire, 'MAX_BYTES', 1), self.assertRaisesRegex(wire.WireError, '^wire-length$'):
            wire.encode(V('text', 'é'))


if __name__ == '__main__':
    unittest.main()
