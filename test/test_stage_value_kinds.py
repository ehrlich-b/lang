#!/usr/bin/env python3
"""Regression tests for STG1 value kinds and their frozen encodings."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import stage_protocol as wire

V = wire.Value


class ValueKindTests(unittest.TestCase):
    def test_invalid_kinds(self):
        for kind in ([], {}, True, 1, None, 'unknown'):
            with self.subTest(kind=kind):
                with self.assertRaises(wire.WireError):
                    wire.encode(V(kind))

    def test_nested_invalid_kinds(self):
        for container in (V('list', [V([])]), V('record', {'x': V({})}),
                          V('descriptor', {'x': V(None)})):
            with self.subTest(container=container):
                with self.assertRaises(wire.WireError):
                    wire.encode(container)

    def test_frozen_encodings(self):
        fixtures = [
            (V('null'), '0000000000'),
            (V('bool', True), '010100000001'),
            (V('i8', -2), '0201000000fe'),
            (V('i16', -2), '0302000000feff'),
            (V('i32', -2), '0404000000feffffff'),
            (V('i64', -2), '0508000000feffffffffffffff'),
            (V('bytes', b'\x00\xff'), '060200000000ff'),
            (V('text', 'é'), '0702000000c3a9'),
            (V('list', [V('null')]), '0809000000010000000000000000'),
            (V('record', {'x': V('bool', True)}), '091000000001000000070100000078010100000001'),
            (V('syntax', '(program)'), '0a090000002870726f6772616d29'),
            (V('descriptor', {}), '0b0400000000000000'),
        ]
        self.assertEqual({v.kind for v, _ in fixtures}, set(wire.TAGS))
        for value, hex_bytes in fixtures:
            with self.subTest(kind=value.kind):
                expected = bytes.fromhex(hex_bytes)
                self.assertEqual(wire.encode(value), expected)
                self.assertEqual(wire.decode(expected), value)
                self.assertEqual(wire.encode(wire.decode(expected)), expected)

    def test_existing_guards(self):
        for value in (None, V('bool', 1), V('i8', 128), V('text', b'x'),
                      V('list', ()), V('record', {1: V('null')})):
            with self.subTest(value=value):
                with self.assertRaises(wire.WireError):
                    wire.encode(value)
        children = []
        cycle = V('list', children)
        children.append(cycle)
        with self.assertRaises(wire.WireError):
            wire.encode(cycle)
        deep = V('null')
        for _ in range(wire.MAX_DEPTH + 1):
            deep = V('list', [deep])
        with self.assertRaises(wire.WireError):
            wire.encode(deep)
        with self.assertRaises(wire.WireError):
            wire.encode(V('list', [V('null')] * (wire.MAX_ITEMS + 1)))


if __name__ == '__main__':
    unittest.main()
