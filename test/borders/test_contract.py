#!/usr/bin/env python3
"""Small oracle tests; no compiler build or grid regeneration."""
import json
from pathlib import Path
import tempfile
import unittest

import render
from run import Probe


class ScriptedProbe(Probe):
    def __init__(self, scratch, replies):
        super().__init__('compiler', scratch)
        self.replies = iter(replies)

    def run(self, command, env):
        code, out, err = next(self.replies)
        self.steps.append(dict(command=command, exit_code=code, stdout=out, stderr=err))
        return code, out, err


class Contract(unittest.TestCase):
    def measure(self, replies, target='llvm', diagnostic=None):
        spec = dict(fixture='test/borders/cases/lang_integers.lang', expected_exit=42, expected_stdout='')
        if diagnostic:
            spec['diagnostic'] = diagnostic
        with tempfile.TemporaryDirectory() as temp:
            return ScriptedProbe(temp, replies).measure('lang', 'integers', target, spec)

    def test_exit_and_output_both_matter(self):
        self.assertEqual(self.measure([(0, '', ''), (0, '', ''), (42, '', '')])['status'], 'supported')
        self.assertEqual(self.measure([(0, '', ''), (0, '', ''), (42, 'unexpected', '')])['status'], 'wrong')
        self.assertEqual(self.measure([(0, '', ''), (0, '', ''), (0, '', '')])['status'], 'wrong')

    def test_link_rejections_keep_diagnostics(self):
        result = self.measure([(0, '', ''), (1, '', 'undefined symbol')])
        self.assertEqual((result['status'], result['phase'], result['detail']), ('rejected', 'link', 'undefined symbol'))

    def test_trap_is_never_a_pass(self):
        result = self.measure([(0, '', ''), (139, '', 'borders: wasm trap')], target='wasm')
        self.assertEqual(result['status'], 'crash')

    def test_wrapper_location_cannot_substitute_for_guest_location(self):
        self.assertEqual(self.measure([(1, '', 'wrapper.lang:8:1: error')], diagnostic='guest:2:8:')['status'], 'wrong')
        self.assertEqual(self.measure([(1, '', 'guest:2:8: invalid token')], diagnostic='guest:2:8:')['status'], 'supported')

    def test_renderer_rejects_hand_edits_and_false_totals(self):
        data = dict(cells=[dict(reader='lang', feature='integers', target='llvm', status='supported', fixture='probe.lang')], totals={'supported': 1})
        expected = render.render(data)
        self.assertIn('| not-run-here |', expected)
        self.assertIn('Totals: supported: 1.', expected)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'BORDERS.md'
            path.write_text(expected)
            render.check(path, expected)
            path.write_text(expected.replace('supported', 'wrong'))
            with self.assertRaises(ValueError):
                render.check(path, expected)
        data['totals']['supported'] = 2
        with self.assertRaises(ValueError):
            render.render(data)


if __name__ == '__main__':
    unittest.main()
