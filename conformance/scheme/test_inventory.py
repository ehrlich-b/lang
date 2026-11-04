import unittest
from inventory import tests


class InventoryTests(unittest.TestCase):
    def test_nested_and_comments(self):
        source = '''; (test 0 0)
        #| (test 0 0) #| nested |# |#
        (let () (test "(;)" (f #\\) 1)))
        '(test 2 2)'''
        self.assertEqual(len(list(tests(source))), 1)

    def test_strings_and_escaped_identifiers(self):
        self.assertEqual(len(list(tests('(test |"| "a\\\"b")'))), 1)

    def test_incomplete_input_fails(self):
        with self.assertRaises(ValueError):
            list(tests('(test 1'))


if __name__ == '__main__':
    unittest.main()
