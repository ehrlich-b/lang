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

    def test_unused_initializer_effect(self):
        source = '(define x 0) (define ignored (begin (set! x 1) 99)) (test 0 x)'
        _, contexts = inventory(source)
        self.assertEqual(contexts[0], '(define x 0)\n'
                         '(define ignored (begin (set! x 1) 99))\n(test-result 0 0 x)')

    def test_indirect_initializer_effect(self):
        source = '(define x 0) (define (mutate) (set! x 1)) (define ignored (mutate)) (test 1 x)'
        _, contexts = inventory(source)
        self.assertIn('(define ignored (mutate))', contexts[0])
        self.assertIn('(define (mutate) (set! x 1))', contexts[0])

    def test_earlier_stateful_test_is_translated(self):
        _, contexts = inventory('(define x 0) (test 1 (begin (set! x 1) x)) (test 1 x)')
        self.assertIn('(begin 1 (begin (set! x 1) x) #f)', contexts[1])
        self.assertNotIn('(test ', contexts[1])

    def test_redefinitions_preserve_initialization_order(self):
        _, contexts = inventory('(define x 0) (define y x) (define x 1) (test 0 y)')
        self.assertEqual(contexts[0], '(define x 0)\n(define y x)\n'
                         '(define x 1)\n(test-result 0 0 y)')

    def test_long_quote_is_data(self):
        _, contexts = inventory('(test \'(test 0 0) (quote (test 0 0)))')
        self.assertEqual(list(contexts), [0])
        self.assertIn('(quote (test 0 0))', contexts[0])


if __name__ == '__main__':
    unittest.main()
