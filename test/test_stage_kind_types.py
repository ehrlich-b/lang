#!/usr/bin/env python3
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from stage_protocol import Value, WireError, frame, unframe


class KindTypesTest(unittest.TestCase):
    def test_invalid_kinds(self):
        value = Value('list', [Value('i8', 7)])
        original = [Value('i8', 7)]
        valid_frame = frame(value)
        for kind in (True, False, 1.0, '1', [], {}, -1, 0, 4, 2**32):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(WireError, '^frame-kind$'):
                    frame(value, kind)
                with self.assertRaisesRegex(WireError, '^frame-kind$'):
                    unframe(valid_frame, kind)
                # Argument validation precedes parsing even on malformed data.
                with self.assertRaisesRegex(WireError, '^frame-kind$'):
                    unframe(b'', kind)
                self.assertEqual(value.data, original)
                self.assertEqual(valid_frame, frame(value))

    def test_canonical_frames_and_default(self):
        value = Value('null')
        fixtures = (
            '535447310500000001000000000000000000000000',
            '535447310500000002000000000000000000000000',
            '535447310500000003000000000000000000000000',
        )
        for kind, expected in enumerate(fixtures, 1):
            with self.subTest(kind=kind):
                wire = bytes.fromhex(expected)
                self.assertEqual(frame(value, kind), wire)
                self.assertEqual(unframe(wire, kind), value)
                self.assertEqual(unframe(wire), value)
                self.assertEqual(wire, bytes.fromhex(expected))
        self.assertEqual(frame(value), bytes.fromhex(fixtures[0]))

    def test_malformed_diagnostics(self):
        wire = frame(Value('null'))
        cases = ((b'', 'frame-header'), (b'BAD!' + wire[4:], 'frame-version'),
                 (wire[:4] + b'\x06' + wire[5:], 'frame-length'),
                 (wire[:-1], 'frame-length'), (wire[:16] + b'\xff' + wire[17:], 'value-length-or-tag'))
        for data, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                with self.assertRaisesRegex(WireError, '^' + diagnostic + '$'):
                    unframe(data)
        with self.assertRaisesRegex(WireError, '^frame-kind$'):
            unframe(wire, 2)


if __name__ == '__main__':
    unittest.main()
