#!/usr/bin/env python3
"""Small oracle tests; no compiler build or grid regeneration."""
import json
import importlib.util
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import render
from run import Probe, declaration_spans, reduce_bug, reduction_candidates

website_spec = importlib.util.spec_from_file_location('generate_borders', render.ROOT / 'web/generate_borders.py')
website = importlib.util.module_from_spec(website_spec)
website_spec.loader.exec_module(website)


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

    def test_minimality_rejects_and_removes_unused_main(self):
        source = Path('test/borders/cases/flow_error_location.lang').read_text()
        spec = dict(fixture='test/borders/cases/flow_error_location.lang',
                    expected_exit=0, expected_stdout='', diagnostic='guest:2:22:')
        protected = {'include "example/flow/flow.lang"'}
        with tempfile.TemporaryDirectory() as temp:
            probe = ScriptedProbe(temp, [(1, '', 'invalid expression')] * 3)
            cell = probe.measure('flow', 'error_location', 'llvm', spec)
            trial = Path(temp) / 'reduced.lang'
            with self.assertRaisesRegex(SystemExit, 'nonminimal declaration.*func main'):
                reduce_bug(probe, 'flow', 'error_location', 'llvm', spec, cell,
                           source, protected, trial, verify=True)
            reduced, trials = reduce_bug(probe, 'flow', 'error_location', 'llvm', spec,
                                         cell, source, protected, trial)
            self.assertEqual(reduced, source[:source.index('func main')])
            self.assertEqual(len(reduced.encode()), 68)
            self.assertEqual([(r['kind'], r['reproduces']) for r in trials], [('declaration', True)])
            self.assertEqual(list(reduction_candidates(reduced, protected)), [])

    def test_declaration_boundaries_preserve_reader_bodies(self):
        reader = '#flow{\nfunc guest() { return 1 + ; }\n}\n'
        declarations = [
            'pub func helper() i64 {\n  // } ignored\n  if true { puts("}\\\"{"); }\n  return 0;\n}\n',
            'extern func puts(s *u8) i64;\n',
            'struct Pair { x i64; y i64; }\n',
            'var n i64 = #calc{ 19 + 23 };\n',
        ]
        source = reader + ''.join(declarations)
        self.assertEqual([source[a:b] for a, b in declaration_spans(source)], declarations)
        source = 'include "reader.lang"\ninclude "runtime.lang"\n' + source
        candidates = list(reduction_candidates(source, {'include "reader.lang"'}))
        self.assertEqual([kind for kind, _, _ in candidates], ['include'] + ['declaration'] * 4)
        self.assertEqual(source[candidates[0][1]:candidates[0][2]], 'include "runtime.lang"\n')

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

    def test_website_regeneration_and_freshness(self):
        cell = dict(reader='minipy', feature='functions', target='wasm', status='supported')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'web').mkdir()
            grid = root / 'borders.json'
            page = root / 'web/index.html'
            prefix, suffix = '<header>keep</header>\n', '\n<footer>keep</footer>'
            page.write_text(prefix + website.START + '\nstale\n' + website.END + suffix)
            with patch.object(website, 'ROOT', root):
                for cells in ([], [cell], *[
                        [dict(cell, feature=f'cross_reader_call_{i}') for i in range(count)]
                        for count in (website.PREVIEW_LIMIT, website.PREVIEW_LIMIT + 1)]):
                    grid.write_text(json.dumps(dict(cells=cells)))
                    with patch.object(sys, 'argv', ['generate_borders.py', '--check']):
                        with self.assertRaisesRegex(SystemExit, 'borders section is stale'):
                            website.main()
                    with patch.object(sys, 'argv', ['generate_borders.py']):
                        website.main()
                    with patch.object(sys, 'argv', ['generate_borders.py', '--check']):
                        website.main()
                    text = page.read_text()
                    self.assertTrue(text.startswith(prefix) and text.endswith(suffix))
                    self.assertIn(f'{len(cells)} tested combinations', text)
                    self.assertEqual(text.count('class="border-cell"'), len(cells))
                    if len(cells) > website.PREVIEW_LIMIT:
                        self.assertIn('<summary>+1 more</summary>', text)
                    else:
                        self.assertNotIn('<details>', text)
                    if cells:
                        self.assertIn('wasm · supported', text)
                page.write_text(page.read_text().replace('wasm · supported', 'wasm · rejected', 1))
                with patch.object(sys, 'argv', ['generate_borders.py', '--check']):
                    with self.assertRaisesRegex(SystemExit, 'borders section is stale'):
                        website.main()

    def test_document_gate_also_rejects_stale_website(self):
        data = dict(cells=[dict(reader='minipy', feature='functions', target='wasm',
                               status='supported', fixture='probe.lang')], totals={'supported': 1})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ('test/borders', 'web', 'docs'):
                (root / directory).mkdir(parents=True)
            (root / 'test/borders/render.py').write_text(Path(render.__file__).read_text())
            (root / 'web/generate_borders.py').write_text(Path(website.__file__).read_text())
            (root / 'borders.json').write_text(json.dumps(data))
            (root / 'docs/BORDERS.md').write_text(render.render(data))
            page = root / 'web/index.html'
            page.write_text(website.START + '\nstale\n' + website.END)
            command = [sys.executable, '-B', str(root / 'test/borders/render.py')]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('borders section is stale', result.stderr)
            with patch.object(website, 'ROOT', root):
                page.write_text(website.render())
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
