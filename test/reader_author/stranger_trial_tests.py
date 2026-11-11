#!/usr/bin/env python3
"""Small diagnostic relocation controls; no SDK build or external inputs needed."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest

from stranger_trial import check_record, diagnostic_root


class DiagnosticRelocationTests(unittest.TestCase):
    def setUp(self):
        self.original = Path('/original/public trial')
        self.evidence = Path('/relocated/packet with spaces')
        self.relative = Path('fixtures/missing-equals.conf')
        self.source = self.evidence / self.relative
        self.tail = ":2:9: expected '=', found 4 @18:19\n"
        self.record = dict(file=self.relative.name, exit=1, stdout='',
                           stderr=str(self.original / self.relative) + self.tail)
        self.result = SimpleNamespace(returncode=1, stdout='', stderr=str(self.source) + self.tail)

    def check(self, result=None, record=None, source=None):
        check_record(result or self.result, record or self.record, source or self.source,
                     self.evidence, self.original)

    def test_known_root_and_relocation(self):
        self.assertEqual(diagnostic_root([dict(stderr=''), self.record]), self.original)
        self.check()
        self.evidence = self.original
        self.source = self.original / self.relative
        self.result.stderr = self.record['stderr']
        self.check()

    def test_multiline_token_and_embedded_original_path_remain_exact(self):
        tail = ':2:8: expected string, found "oops\n' + str(self.original) + ' @17:23\n'
        self.record['stderr'] = str(self.original / self.relative) + tail
        self.result.stderr = str(self.source) + tail
        self.check()
        self.result.stderr = self.result.stderr.replace(str(self.original), str(self.evidence))
        with self.assertRaises(AssertionError):
            self.check()

    def test_changed_actual_diagnostics_fail(self):
        mutations = {
            'fixture': ('missing-equals.conf', 'missing-bracket.conf'),
            'directory': ('/fixtures/', '/other-fixtures/'),
            'root': ('/relocated/', '/wrong-root/'),
            'line': (':2:9:', ':3:9:'),
            'column': (':2:9:', ':2:10:'),
            'expected token': ("expected '='", "expected ']'"),
            'found token': ('found 4', 'found 5'),
            'span': ('@18:19', '@18:20'),
            'whitespace': ('expected ', 'expected  '),
            'trailing newline': ('\n', ''),
        }
        for label, (old, new) in mutations.items():
            with self.subTest(label=label), self.assertRaises(AssertionError):
                result = deepcopy(self.result)
                result.stderr = result.stderr.replace(old, new)
                self.check(result=result)
        for text in ('', self.result.stderr + 'additional stderr\n'):
            with self.subTest(stderr=text), self.assertRaises(AssertionError):
                self.check(result=SimpleNamespace(returncode=1, stdout='', stderr=text))

    def test_changed_golden_fixture_or_source_fails(self):
        record = deepcopy(self.record)
        record['stderr'] = record['stderr'].replace('missing-equals.conf', 'other.conf')
        with self.assertRaises(AssertionError):
            self.check(record=record)
        for relative in ('other/missing-equals.conf', 'fixtures/other.conf'):
            with self.subTest(source=relative), self.assertRaises(AssertionError):
                self.check(source=self.evidence / relative)

    def test_exit_and_stdout_stay_exact(self):
        for field, value in (('returncode', 0), ('returncode', 2), ('stdout', '\n')):
            result = deepcopy(self.result)
            setattr(result, field, value)
            with self.subTest(field=field, value=value), self.assertRaises(AssertionError):
                self.check(result=result)

    def test_success_still_requires_empty_stderr(self):
        record = dict(file='sample.conf', exit=0, stdout='valid\n', stderr='')
        result = SimpleNamespace(returncode=0, stdout='valid\n', stderr='')
        self.check(result=result, record=record)
        result.stderr = str(self.source) + self.tail
        with self.assertRaises(AssertionError):
            self.check(result=result, record=record)


if __name__ == '__main__':
    unittest.main(verbosity=2)
