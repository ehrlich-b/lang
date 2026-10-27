#!/usr/bin/env python3
"""Encoded value budgets include each value's tag and length header."""
import copy
import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import stage_protocol as wire

V = wire.Value


class TotalSizeTests(unittest.TestCase):
    def check_boundary(self, exact, oversized, budget=32):
        before = copy.deepcopy((exact, oversized))
        with patch.object(wire, 'MAX_BYTES', budget):
            encoded = wire.encode(exact)
            self.assertEqual(len(encoded), budget)
            self.assertEqual(wire.decode(encoded), exact)
            framed = wire.frame(exact)
            self.assertEqual(len(framed), budget + wire.HEADER.size)
            self.assertEqual(wire.unframe(framed), exact)
            self.assertEqual(wire.read_frame(io.BytesIO(framed)), framed)
            with self.assertRaisesRegex(wire.WireError, 'wire-length'):
                wire.encode(oversized)
        self.assertEqual((exact, oversized), before)

    def test_bytes_and_text_boundaries(self):
        self.check_boundary(V('bytes', b'x' * 27), V('bytes', b'x' * 28))
        # UTF-8 byte length, rather than character count, determines the budget.
        self.check_boundary(V('text', 'é' * 13 + 'x'), V('text', 'é' * 14))
        self.check_boundary(V('syntax', '(program' + 'x' * 19),
                            V('syntax', '(program' + 'x' * 20))

    def test_container_boundaries(self):
        self.check_boundary(V('list', [V('bytes', b'x' * 18)]),
                            V('list', [V('bytes', b'x' * 19)]))
        self.check_boundary(V('record', {'a': V('bytes', b'x' * 12)}),
                            V('record', {'a': V('bytes', b'x' * 13)}))
        self.check_boundary(V('descriptor', {'a': V('list', [V('bytes', b'x' * 3)])}),
                            V('descriptor', {'a': V('list', [V('bytes', b'x' * 4)])}))

    def test_default_limit(self):
        budget = wire.MAX_BYTES
        value = V('bytes', b'x' * (budget - 5))
        encoded = wire.encode(value)
        self.assertEqual(len(encoded), budget)
        self.assertEqual(wire.decode(encoded), value)
        with self.assertRaisesRegex(wire.WireError, 'wire-length'):
            wire.encode(V('bytes', b'x' * (budget - 4)))
        self.assertEqual(wire.MAX_BYTES, budget)

    def test_canonical_encoding(self):
        value = V('record', {'z': V('null'), 'a': V('bytes', b'X')})
        expected = (b'\x09\x1b\x00\x00\x00\x02\x00\x00\x00'
                    b'\x07\x01\x00\x00\x00a\x06\x01\x00\x00\x00X'
                    b'\x07\x01\x00\x00\x00z\x00\x00\x00\x00\x00')
        self.assertEqual(wire.encode(value), expected)
        self.assertEqual(wire.decode(expected), value)


if __name__ == '__main__':
    unittest.main()
