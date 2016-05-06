"""
Tests for utility functions
"""
import warnings
import unittest

from ads.utils import cached_property


class TestUtils(unittest.TestCase):
    """
    Test utility functions
    """

    def test_cached_property(self):
        """
        Test that the cached property raises a warning when __get__ is accessed
        """
        class DummyClass(object):
            @cached_property
            def lazy_attribute(self):
                return 1

        dc = DummyClass()
        with warnings.catch_warnings(record=True) as w:
            dc.lazy_attribute
            self.assertEqual(len(w), 1)

            # Should only print once unless the filter is changed
            dc.lazy_attribute
            self.assertEqual(len(w), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
