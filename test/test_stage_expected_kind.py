#!/usr/bin/env python3
"""Expected frame kinds are validated independently of the wire header."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from stage_protocol import Value, WireError, unframe

# Frozen wire bytes, independent of the frame encoder: a text value "hi".
FRAMES = (
    bytes.fromhex('5354473107000000010000000000000007020000006869'),
    bytes.fromhex('5354473107000000020000000000000007020000006869'),
    bytes.fromhex('5354473107000000030000000000000007020000006869'),
)


class ExpectedKindTests(unittest.TestCase):
    def test_invalid_expected_kinds(self):
        for expected in (True, False, 1.0, 2.0, '1', [], {}, 0, 4):
            for raw in FRAMES:
                with self.subTest(expected=expected, raw=raw):
                    data = bytearray(raw)
                    with self.assertRaisesRegex(WireError, '^frame-kind$'):
                        unframe(data, expected)
                    self.assertEqual(data, raw)

    def test_valid_expected_kinds(self):
        for actual, raw in enumerate(FRAMES, 1):
            for expected in (None, 1, 2, 3):
                with self.subTest(actual=actual, expected=expected):
                    data = bytearray(raw)
                    if expected is None or expected == actual:
                        self.assertEqual(unframe(data, expected), Value('text', 'hi'))
                    else:
                        with self.assertRaisesRegex(WireError, '^frame-kind$'):
                            unframe(data, expected)
                    self.assertEqual(data, raw)

    def test_invalid_kind_is_checked_before_frame(self):
        with self.assertRaisesRegex(WireError, '^frame-kind$'):
            unframe(b'', True)


if __name__ == '__main__':
    unittest.main()
