#!/usr/bin/env python3
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
import stage_protocol as protocol


class IntSubclass(int):
    pass


class StageFrameKindTests(unittest.TestCase):
    def setUp(self):
        self.value = protocol.Value('null')

    def test_valid_kinds_have_exact_wire_bytes_and_round_trip(self):
        for kind in (1, 2, 3):
            with self.subTest(kind=kind):
                expected = (b'STG1\x05\x00\x00\x00' + bytes([kind]) +
                            b'\x00\x00\x00\x00\x00\x00\x00' +
                            b'\x00\x00\x00\x00\x00')
                self.assertEqual(protocol.frame(self.value, kind), expected)
                self.assertEqual(protocol.unframe(expected, kind), self.value)
                self.assertEqual(protocol.unframe(expected), self.value)
                for other in (1, 2, 3):
                    if other != kind:
                        with self.assertRaisesRegex(protocol.WireError, '^frame-kind$'):
                            protocol.unframe(expected, other)

    def test_default_and_none_policy(self):
        raw = protocol.frame(self.value, 1)
        self.assertEqual(protocol.frame(self.value), raw)
        self.assertEqual(protocol.unframe(raw, None), self.value)
        with self.assertRaisesRegex(protocol.WireError, '^frame-kind$'):
            protocol.frame(self.value, None)

    def test_invalid_kinds_rejected_before_encoding(self):
        for kind in (True, False, 1.0, 1.5, '1', '', 0, 4, -1, IntSubclass(1)):
            with self.subTest(kind=kind, type=type(kind)):
                with patch.object(protocol, 'encode') as encode:
                    with self.assertRaisesRegex(protocol.WireError, '^frame-kind$'):
                        protocol.frame(self.value, kind)
                    encode.assert_not_called()
                with self.assertRaisesRegex(protocol.WireError, '^frame-kind$'):
                    protocol.unframe(protocol.frame(self.value), kind)


if __name__ == '__main__':
    unittest.main()
