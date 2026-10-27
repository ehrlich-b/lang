#!/usr/bin/env python3
"""Regression tests for bounded reads of STG1 frames."""
import io
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from stage_protocol import HEADER, Value, WireError, frame, read_frame


class Fragmented(io.BytesIO):
    def __init__(self, data, mutable=False):
        super().__init__(data)
        self.mutable = mutable
        self.requests = []

    def read(self, size=-1):
        self.requests.append(size)
        result = super().read(min(size, 1))
        return bytearray(result) if self.mutable else result


class Scripted:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.requests = []

    def read(self, size):
        self.requests.append(size)
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


class ReadFrameTests(unittest.TestCase):
    def setUp(self):
        self.first = frame(Value('text', 'first'))
        self.second = frame(Value('bytes', b'second'))

    def test_fragmented_concatenated_frames(self):
        for mutable in (False, True):
            with self.subTest(mutable=mutable):
                stream = Fragmented(self.first + self.second, mutable)
                self.assertEqual(read_frame(stream), self.first)
                self.assertEqual(stream.tell(), len(self.first))
                self.assertEqual(len(stream.requests), len(self.first))
                self.assertEqual(read_frame(stream), self.second)
                self.assertEqual(stream.tell(), len(self.first) + len(self.second))
                self.assertEqual(len(stream.requests), len(self.first) + len(self.second))
                self.assertTrue(all(n > 0 for n in stream.requests))

    def test_malformed_chunks_in_header_and_body(self):
        for bad in ('x', '', 1, 0, None, [1], memoryview(b'x')):
            for prefix in ((), (self.first[:HEADER.size],)):
                with self.subTest(bad=repr(bad), body=bool(prefix)):
                    stream = Scripted(*prefix, bad)
                    with self.assertRaises(WireError):
                        read_frame(stream)
                    self.assertEqual(len(stream.requests), len(prefix) + 1)

    def test_oversized_chunks_in_header_and_body(self):
        for responses in ((self.first[:HEADER.size + 1],),
                          (self.first[:HEADER.size], self.first[HEADER.size:] + b'x')):
            for mutable in (False, True):
                with self.subTest(body=len(responses) == 2, mutable=mutable):
                    stream = Scripted(*(bytearray(x) if mutable else x for x in responses))
                    with self.assertRaises(WireError):
                        read_frame(stream)
                    self.assertEqual(len(stream.requests), len(responses))

    def test_eof_and_truncation(self):
        for data in (b'', self.first[:3], self.first[:HEADER.size], self.first[:-1]):
            with self.subTest(length=len(data)):
                with self.assertRaisesRegex(WireError, 'truncated-frame'):
                    read_frame(io.BytesIO(data))

    def test_io_errors_propagate(self):
        for prefix in ((), (self.first[:HEADER.size],)):
            with self.subTest(body=bool(prefix)):
                error = OSError('injected')
                stream = Scripted(*prefix, error)
                with self.assertRaises(OSError) as raised:
                    read_frame(stream)
                self.assertIs(raised.exception, error)
                self.assertEqual(len(stream.requests), len(prefix) + 1)


if __name__ == '__main__':
    unittest.main()
