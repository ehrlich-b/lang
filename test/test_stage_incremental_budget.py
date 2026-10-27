#!/usr/bin/env python3
"""Container byte budgets are enforced before visiting subsequent children."""
import copy
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import stage_protocol as wire

V = wire.Value


class IncrementalBudgetTests(unittest.TestCase):
    def test_overbudget_prefix_precedes_invalid_child(self):
        invalid = V('bool', 'invalid')
        cases = [
            V('list', [V('bytes', b'1234567'), invalid]),
            V('record', {'a': V('bytes', b'1234567'), 'b': invalid}),
            V('descriptor', {'a': V('bytes', b'1234567'), 'b': invalid}),
            # The key alone exceeds the container budget before its value.
            V('record', {'abcdefgh': invalid}),
            V('descriptor', {'abcdefgh': invalid}),
            # A completed nested child can also overflow its parent's prefix.
            V('list', [V('list', [V('null')]), invalid]),
            # The nested list must enforce its own prefix before its invalid child.
            V('list', [V('list', [V('bytes', b'1234567'), invalid])]),
        ]
        for value in cases:
            with self.subTest(value=value), patch.object(wire, 'MAX_BYTES', 20):
                before = copy.deepcopy(value)
                with self.assertRaisesRegex(wire.WireError, '^wire-length$'):
                    wire.encode(value)
                self.assertEqual(value, before)

    def test_exact_bytes_and_roundtrips(self):
        cases = [
            (V('list', [V('null'), V('bool', True)]),
             b'\x08\x0f\x00\x00\x00\x02\x00\x00\x00'
             b'\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x01'),
            (V('record', {'z': V('null'), 'a': V('bool', True)}),
             b'\x09\x1b\x00\x00\x00\x02\x00\x00\x00'
             b'\x07\x01\x00\x00\x00a\x01\x01\x00\x00\x00\x01'
             b'\x07\x01\x00\x00\x00z\x00\x00\x00\x00\x00'),
            (V('descriptor', {'a': V('list', [V('null')])}),
             b'\x0b\x18\x00\x00\x00\x01\x00\x00\x00'
             b'\x07\x01\x00\x00\x00a\x08\x09\x00\x00\x00'
             b'\x01\x00\x00\x00\x00\x00\x00\x00\x00'),
        ]
        for value, expected in cases:
            with self.subTest(kind=value.kind), patch.object(wire, 'MAX_BYTES', len(expected)):
                before = copy.deepcopy(value)
                self.assertEqual(wire.encode(value), expected)
                self.assertEqual(wire.decode(expected), value)
                self.assertEqual(value, before)

    def test_shared_subvalues_and_cycles(self):
        shared = V('list', [V('null')])
        value = V('list', [shared, shared])
        before = copy.deepcopy(value)
        self.assertEqual(wire.decode(wire.encode(value)), value)
        self.assertEqual(value, before)
        self.assertIs(value.data[0], value.data[1])
        cycle = V('list', [])
        cycle.data.append(cycle)
        with self.assertRaisesRegex(wire.WireError, '^cyclic-wire-object$'):
            wire.encode(cycle)
        self.assertIs(cycle.data[0], cycle)


if __name__ == '__main__':
    unittest.main()
