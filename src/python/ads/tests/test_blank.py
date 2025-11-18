import warnings
import unittest


class TestBlank(unittest.TestCase):
    """
    Test blank.
    """

    def test_blank(self):
        self.assertEqual(1, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
