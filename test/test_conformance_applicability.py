#!/usr/bin/env python3
"""Regression cases for frozen target predicates and optimization exclusions."""
import json
import unittest
from conformance_applicability import ROOT, classify, selector


class ApplicabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {r['path']: r for r in json.loads((ROOT / 'C3.json').read_text())['cases']}

    def test_architecture_and_data_model(self):
        expected = {
            'compile/20111209-1.c': ('platform-skip', 'platform-skip'),
            'compile/pr96998.c': ('platform-skip', 'eligible'),
            'compile/pr65680.c': ('eligible', 'eligible'),
            'compile/mipscop-4.c': ('platform-skip', 'platform-skip'),
            'compile/103818.c': ('eligible', 'eligible'),
            'compile/pr88347.c': ('platform-skip', 'platform-skip'),
        }
        for path, statuses in expected.items():
            for target, status in zip(('x86_64-linux-gnu', 'arm64-apple-macos'), statuses):
                for opt in ('-O0', '-O2'):
                    with self.subTest(path=path, target=target, opt=opt):
                        self.assertEqual(classify(self.cases[path], target, opt), status)

    def test_wildcard_skip_is_option_specific(self):
        for target in ('x86_64-linux-gnu', 'arm64-apple-macos'):
            for path in ('execute/20030216-1.c', 'compile/attr-complex-method.c',
                         'compile/attr-complex-method-2.c'):
                for opt in ('-O0', '-O2'):
                    self.assertEqual(classify(self.cases[path], target, opt), 'eligible')
        # The O0 exclusion applies only to x86-64; the asm capability still
        # needs a reference on every other target/optimization combination.
        case = self.cases['compile/asmgoto-5.c']
        self.assertEqual(classify(case, 'x86_64-linux-gnu', '-O0'), 'platform-skip')
        self.assertEqual(classify(case, 'x86_64-linux-gnu', '-O2'), 'reference-required')
        self.assertEqual(classify(case, 'arm64-apple-macos', '-O0'), 'reference-required')

    def test_unknown_predicates_are_not_skips(self):
        self.assertIsNone(selector('asm_goto_with_outputs', 'aarch64-apple-darwin'))
        self.assertTrue(selector('lp64 || llp64', 'aarch64-apple-darwin'))
        self.assertTrue(selector('ptr32plus && { ! llp64 }', 'x86_64-pc-linux-gnu'))
        self.assertFalse(selector('! { i?86-*-* x86_64-*-* }', 'x86_64-pc-linux-gnu'))
        self.assertIsNone(selector('! unknown_feature', 'x86_64-pc-linux-gnu'))


if __name__ == '__main__':
    unittest.main()
