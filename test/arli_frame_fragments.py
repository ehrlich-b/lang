"""Fragmented STG1 transport regression; run from repository root."""
import io
import sys
import unittest

sys.path.insert(0, str(__import__('pathlib').Path.cwd() / 'src'))
from stage_protocol import HEADER, MAX_BYTES, Value, WireError, frame, read_frame


class arli_frame_fragments_stream(io.BytesIO):
    def read(self, n=-1):
        return super().read(min(n, 1))


class arli_frame_fragments(unittest.TestCase):
    def test_arli_frame_fragments(self):
        first = frame(Value('bytes', b'a\0\xffb'), 1)
        second = frame(Value('text', 'é🦋'), 3)
        stream = arli_frame_fragments_stream(first + second)
        self.assertEqual(read_frame(stream), first)
        self.assertEqual(stream.tell(), len(first))
        self.assertEqual(read_frame(stream), second)
        self.assertEqual(stream.tell(), len(first + second))
        for cut in range(len(first)):
            with self.subTest(cut=cut):
                with self.assertRaisesRegex(WireError, '^truncated-frame$'):
                    read_frame(arli_frame_fragments_stream(first[:cut]))
        for magic, size, kind, reserved in [
            (b'STG2', 1, 1, 0), (b'STG1', MAX_BYTES + 1, 1, 0),
            (b'STG1', 1, 0, 0), (b'STG1', 1, 4, 0), (b'STG1', 1, 1, 1)
        ]:
            with self.subTest(header=(magic, size, kind, reserved)):
                stream = arli_frame_fragments_stream(HEADER.pack(magic, size, kind, reserved) + b'x')
                with self.assertRaisesRegex(WireError, '^frame-header$'):
                    read_frame(stream)
                self.assertEqual(stream.tell(), HEADER.size)


if __name__ == '__main__':
    unittest.main(verbosity=2)
