#!/usr/bin/env python3
"""Positive revision proof and adversarial controls for sealed fixture bytes."""
import copy
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("whitespace", ROOT / "scripts/check_benchmark_whitespace.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class BenchmarkWhitespaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = CHECK.load_baseline(ROOT)
        cls.expected, cls.mapping = CHECK.expected_revision(cls.originals)

    def setUp(self):
        # Retain controls and their exact bytes for later inspection.
        self.root = Path(tempfile.mkdtemp(prefix="benchmark-whitespace-"))
        for name, data in self.expected.items():
            path = self.root / CHECK.BENCHMARK / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def path(self, name):
        return self.root / CHECK.BENCHMARK / name

    def check(self, originals=None):
        return CHECK.check_benchmark(self.root, self.originals if originals is None else originals)

    def test_exact_twelve_site_revision(self):
        mapping = self.check()
        self.assertEqual(len(mapping), 12)
        self.assertEqual(set(CHECK.SITES), {f"tasks/R{i:02}/starter.lang" for i in
                                         (8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20)})
        for item in mapping:
            name = str(Path(item["path"]).relative_to(CHECK.BENCHMARK))
            old = self.originals[name]
            new = self.path(name).read_bytes()
            self.assertEqual(len(old) - len(new), 4)
            self.assertEqual(len(old.splitlines()), len(new.splitlines()))
            self.assertEqual(old.split(), new.split())

    def test_non_whitespace_edit_rejected_even_with_checksum(self):
        name = "tasks/R08/starter.lang"
        p = self.path(name)
        old_hash = CHECK.digest(p.read_bytes())
        p.write_bytes(p.read_bytes() + b"// altered semantic contract\n")
        m = self.path("SHA256SUMS")
        m.write_bytes(m.read_bytes().replace(old_hash.encode(), CHECK.digest(p.read_bytes()).encode()))
        with self.assertRaisesRegex(CHECK.Invalid, "manifest changes"):
            self.check()

    def test_unrecorded_whitespace_rejected(self):
        p = self.path("tasks/R08/starter.lang")
        p.write_bytes(p.read_bytes() + b"\n")
        with self.assertRaises(CHECK.Invalid):
            self.check()

    def test_omitted_checksum_update_rejected(self):
        self.path("SHA256SUMS").write_bytes(self.originals["SHA256SUMS"])
        with self.assertRaisesRegex(CHECK.Invalid, "checksum mismatch"):
            self.check()

    def test_omitted_site_rejected(self):
        name = "tasks/R20/starter.lang"
        self.path(name).write_bytes(self.originals[name])
        with self.assertRaises(CHECK.Invalid):
            self.check()

    def test_extra_benchmark_file_rejected(self):
        self.path("tasks/R08/extra.lang").write_bytes(b"unexpected\n")
        with self.assertRaisesRegex(CHECK.Invalid, "extra or missing"):
            self.check()

    def test_forged_old_manifest_rejected(self):
        forged = copy.copy(self.originals)
        forged["SHA256SUMS"] = forged["SHA256SUMS"].replace(b"73b1321b", b"00000000", 1)
        with self.assertRaisesRegex(CHECK.Invalid, "forged old manifest"):
            self.check(forged)

    def test_forged_old_starter_rejected(self):
        forged = copy.copy(self.originals)
        forged["tasks/R08/starter.lang"] += b"\n"
        with self.assertRaisesRegex(CHECK.Invalid, "old checksum mismatch"):
            self.check(forged)

    def test_task_metadata_remains_byte_identical(self):
        p = self.path("tasks/R08/task.json")
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaises(CHECK.Invalid):
            self.check()

    def test_every_referenced_checksum_is_checked(self):
        # Also acts as the independent checksum-bypass mutation detector.
        entries = CHECK.parse_manifest(self.path("SHA256SUMS").read_bytes())
        self.assertEqual(len(entries), 68)
        entries.pop(CHECK.OPERATOR)
        for name in entries:
            with self.subTest(name=name):
                p = self.path(name)
                old = p.read_bytes()
                p.write_bytes(old + b"corrupt")
                try:
                    with self.assertRaisesRegex(CHECK.Invalid, "checksum mismatch: " + name):
                        self.check()
                finally:
                    p.write_bytes(old)

    def test_external_checksum_controls(self):
        archive = self.root / "corpus.gz"
        archive.write_bytes(b"external archive fixture")
        entries = {CHECK.OPERATOR: CHECK.digest(archive.read_bytes())}
        CHECK.verify_checksums(self.root / CHECK.BENCHMARK, entries, archive)
        archive.write_bytes(b"corrupt")
        with self.assertRaisesRegex(CHECK.Invalid, "checksum mismatch"):
            CHECK.verify_checksums(self.root / CHECK.BENCHMARK, entries, archive)
        with self.assertRaisesRegex(CHECK.Invalid, "operator archive required"):
            CHECK.verify_checksums(self.root / CHECK.BENCHMARK, entries)

    def test_manifest_path_and_duplicate_controls(self):
        for data in [b"0" * 64 + b"  ../escape\n", b"bad\n",
                     b"0" * 64 + b"  /absolute\n",
                     (b"0" * 64 + b"  same\n") * 2]:
            with self.subTest(data=data), self.assertRaises(CHECK.Invalid):
                CHECK.parse_manifest(data)

    def test_full_pin_required(self):
        with self.assertRaisesRegex(CHECK.Invalid, "full sealed source pin"):
            CHECK.load_baseline(ROOT, "HEAD")

    def test_repository_allowlist_rejects_extra_product_file(self):
        # First prove the exact allowed revision passes in a separate repository.
        for name, data in self.originals.items():
            self.path(name).write_bytes(data)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Bryan Ehrlich",
                        "-c", "user.email=ehrlich.bryan@gmail.com", "commit", "-qm", "Record fixture baseline."],
                       check=True)
        for name, data in self.expected.items():
            self.path(name).write_bytes(data)
        for name in CHECK.ADDITIONS:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        old_pin = CHECK.BASELINE
        try:
            CHECK.BASELINE = "HEAD"
            CHECK.check_scope(self.root)
            self.root.joinpath("extra-product.txt").write_text("extra\n")
            with self.assertRaisesRegex(CHECK.Invalid, "file allowlist mismatch.*extra-product.txt"):
                CHECK.check_scope(self.root)
        finally:
            CHECK.BASELINE = old_pin


if __name__ == "__main__":
    unittest.main(verbosity=2)
