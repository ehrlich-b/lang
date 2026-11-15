"""Synthetic diagnostic rubric examples, independent of measured output."""
import unittest

from check import PROPERTIES, score_diagnostic


class DiagnosticScoring(unittest.TestCase):
    filename = 'missing.tariff'
    source = 'return n + ;\n'

    def score(self, text):
        return score_diagnostic(text, self.filename, self.source)

    def test_positive_and_negative_per_property(self):
        examples = {
            'file': ('/tmp/missing.tariff:1:2: syntax error\n',
                     'tariff:1:2: syntax error\n'),
            'line': ('tariff:1: syntax error\n', 'tariff: syntax error @12:13\n'),
            'column': ('tariff:1:2: syntax error\n', 'tariff:1: syntax error @12:13\n'),
            'expected': ("tariff:1:2: expected number or '('\n",
                         "tariff:1:2: unexpected ';'\n"),
            'caret': ('tariff:1:12: syntax error\nreturn n + ;\n           ^\n',
                      'tariff:1:12: syntax error\nreturn n + ;\n'),
        }
        self.assertEqual(set(examples), set(PROPERTIES))
        for property, (positive, negative) in examples.items():
            with self.subTest(property=property):
                self.assertTrue(self.score(positive)[property])
                self.assertFalse(self.score(negative)[property])

    def test_expected_token_spellings(self):
        for message in ("syntax error, unexpected ID, expecting ';'",
                        "missing ';' at 'return'", "mismatched input ';' expecting INT"):
            with self.subTest(message=message):
                self.assertTrue(self.score('tariff:1:2: ' + message + '\n')['expected'])
        for message in ('token recognition error at: @', 'expected', 'missing operand'):
            with self.subTest(message=message):
                self.assertFalse(self.score('tariff:1:2: ' + message + '\n')['expected'])

    def test_caret_requires_source(self):
        self.assertFalse(self.score('tariff:1:2: syntax error\n ^\n')['caret'])
        self.assertFalse(self.score('tariff:1:2: syntax error\nother source\n ^\n')['caret'])
        self.assertTrue(self.score('tariff:2:1: syntax error\n\n^\n')['caret'])

    def test_only_headers_supply_location_and_expectations(self):
        result = self.score('syntax error @12:13\nmissing.tariff:1:2\nexpected INT\n')
        self.assertFalse(any(result.values()))
        self.assertFalse(self.score('prefix-missing.tariff:1:2: error\n')['file'])
        self.assertFalse(self.score('tariff:0:0: error\n')['line'])

    def test_all_properties_are_independent_booleans(self):
        result = self.score('missing.tariff:1:12: expected INT\nreturn n + ;\n           ^\n')
        self.assertEqual(result, dict.fromkeys(PROPERTIES, True))
        self.assertEqual(self.score(''), dict.fromkeys(PROPERTIES, False))


if __name__ == '__main__':
    unittest.main()
