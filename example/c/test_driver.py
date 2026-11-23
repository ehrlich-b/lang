"""Regression tests for the standalone C reader's output handling."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FIXTURE = HERE / "fixtures" / "layout_and_flow.c"


class BuildOutputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=ROOT / "out")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.source = self.directory / "input.c"
        self.source.write_bytes(FIXTURE.read_bytes())
        self.output = self.directory / "program"

    def build(self, source, output):
        return subprocess.run(
            [sys.executable, "-B", HERE / "driver.py", "build", source, "-o", output],
            cwd=ROOT, capture_output=True, timeout=40,
        )

    def test_replaces_output_links_without_writing_through(self):
        for link in (self.output.symlink_to, lambda path: os.link(path, self.output)):
            with self.subTest(link=link):
                link(self.source)
                result = self.build(self.source, self.output)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.source.read_bytes(), FIXTURE.read_bytes())
                self.assertFalse(self.output.samefile(self.source))
                self.assertFalse(self.output.is_symlink())
                run = subprocess.run([self.output], capture_output=True, check=True, timeout=3)
                self.assertEqual(run.stdout, FIXTURE.with_suffix(".expected").read_bytes())
                self.output.unlink()

    def test_rejects_input_as_output(self):
        self.output.symlink_to(self.source)
        for source, output in ((self.source, self.source), (self.output, self.source),
                               (self.output, self.output)):
            with self.subTest(source=source, output=output):
                result = self.build(source, output)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(b"output path is the input file", result.stderr)
                self.assertEqual(self.source.read_bytes(), FIXTURE.read_bytes())
                self.assertTrue(self.output.is_symlink())

    def test_failed_compile_leaves_output_link_in_place(self):
        self.output.symlink_to(self.source)
        result = self.build(HERE / "fixtures" / "reject_float.c", self.output)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(self.output.is_symlink())
        self.assertEqual(self.source.read_bytes(), FIXTURE.read_bytes())


if __name__ == "__main__":
    unittest.main()
