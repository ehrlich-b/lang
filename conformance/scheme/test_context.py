"""Small syntax/context probes, independent of the upstream corpus."""
import unittest
from inventory import forms, tests, Vector
from score import inventory, render


class ContextTests(unittest.TestCase):
    def test_vectors_and_datum_comments(self):
        source = '#;(test 9 9) (test #(a b) \'#(a b))'
        parsed = list(tests(source))
        self.assertEqual(len(parsed), 1)
        self.assertIsInstance(parsed[0][1], Vector)
        self.assertEqual(render(parsed[0]), "(test #(a b) '#(a b))")

    def test_textual_sites_do_not_earn_passes(self):
        sites, contexts = inventory('; (test 0 0)\n(test "(test 1 1)" "x")')
        self.assertEqual(len(sites), 3)
        self.assertEqual(list(contexts), [1])

    def test_lexical_and_definition_context(self):
        source = '(define (f x) (+ x 4)) (let ((x 2)) (test 6 (f x)))'
        _, contexts = inventory(source)
        self.assertIn('(define (f x) (+ x 4))', contexts[0])
        self.assertIn('(let ((x 2)) (test-result 0 6 (f x)))', contexts[0])


if __name__ == '__main__':
    unittest.main()
