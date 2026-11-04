"""Guard the coverage denominator and distinguish reach from call counts."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("coverage_functions", ROOT / "scripts/coverage_functions.py")
coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(coverage)

IR = """define i64 @cold() {
entry:
  ; comment
  ret i64 0
}
define i64 @hot() {
entry:
  ret i64 1
}
"""
PROFILE = """Counters:
  cold:
    Hash: 0x1
    Counters: 1
    Block counts: [0]
  hot:
    Hash: 0x2
    Counters: 2
    Block counts: [0, 7]
"""


class CoverageTests(unittest.TestCase):
    def test_ir_pgo_counter_order_and_zero_denominator(self):
        sources = {name: {"source": "probe.lang", "line": i}
                   for i, name in enumerate(("cold", "hot"), 1)}
        report = coverage.summarize(IR, PROFILE, sources)
        self.assertEqual((report["executed"], report["total"]), (1, 2))
        self.assertEqual(report["per_source"], {"probe.lang": {"executed": 1, "total": 2}})
        self.assertEqual(report["never_executed"], [dict(name="cold", source="probe.lang", line=1, ir_body_lines=1)])

    def test_missing_counters_or_source_fail_loudly(self):
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            coverage.summarize(IR, PROFILE.split("  hot:")[0], {})
        with self.assertRaisesRegex(ValueError, "without source"):
            coverage.summarize(IR, PROFILE, {})
        with self.assertRaisesRegex(ValueError, "empty IR profile"):
            coverage.profile_functions("not a profile")

    def test_only_real_declarations_in_include_closure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.lang").write_text('include "b.lang"\ninclude "b.lang"\n'
                '// func comment() {}\n/* func block() {} */\n'
                'var s *u8 = "func quoted() {}";\nvar c i64 = \'"\';\n'
                'extern func external();\nfunc a() {}\n')
            (root / "b.lang").write_text('include "a.lang"\nfunc b() {}\n')
            result = coverage.source_functions(root, ["a.lang"])
            self.assertEqual(set(result), {"a", "b"})
            self.assertEqual(result["b"], {"source": "b.lang", "line": 2})


if __name__ == "__main__":
    unittest.main()
