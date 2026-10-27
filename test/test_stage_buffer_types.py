#!/usr/bin/env python3
"""Public wire decoders accept only binary buffers without modifying them."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
import stage_protocol as wire


class BufferTypesTest(unittest.TestCase):
    def test_invalid_types(self):
        payload = wire.encode(wire.Value('text', 'hello'))
        frame = wire.frame(wire.Value('text', 'hello'))
        for decoder, valid in ((wire.decode, payload), (wire.unframe, frame)):
            impostors = ['', 'x' * len(valid), [], list(valid), {},
                         {'x': 1}, 0, 1, None, memoryview(b''), memoryview(valid)]
            for data in impostors:
                with self.subTest(decoder=decoder.__name__, data=repr(data)):
                    before = data.tobytes() if isinstance(data, memoryview) else copy.deepcopy(data)
                    with self.assertRaisesRegex(wire.WireError, '^wire-type$'):
                        decoder(data)
                    after = data.tobytes() if isinstance(data, memoryview) else data
                    self.assertEqual(after, before)

    def test_binary_controls_and_no_mutation(self):
        value = wire.Value('record', {'a': wire.Value('bytes', b'\x00\xff'),
                                      'z': wire.Value('list', [wire.Value('text', 'hi')])})
        for decoder, encoded in ((wire.decode, wire.encode(value)),
                                 (wire.unframe, wire.frame(value))):
            for constructor in (bytes, bytearray):
                with self.subTest(decoder=decoder.__name__, constructor=constructor):
                    data = constructor(encoded)
                    before = bytes(data)
                    self.assertEqual(decoder(data), value)
                    self.assertEqual(bytes(data), before)

    def test_malformed_binary_diagnostics(self):
        for constructor in (bytes, bytearray):
            for decoder, data, message in (
                (wire.decode, b'', 'value-header'),
                (wire.decode, b'\xff\x00\x00\x00\x00', 'value-length-or-tag'),
                (wire.unframe, b'', 'frame-header'),
                (wire.unframe, b'BAD!' + b'\x00' * 12, 'frame-version'),
            ):
                with self.subTest(decoder=decoder.__name__, constructor=constructor, message=message):
                    data = constructor(data)
                    before = bytes(data)
                    with self.assertRaisesRegex(wire.WireError, '^' + message + '$'):
                        decoder(data)
                    self.assertEqual(bytes(data), before)


if __name__ == '__main__':
    unittest.main()
