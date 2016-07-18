"""
Tests for utility functions
"""
import mock
import unittest

from ads.utils import cached_property


class DummyClass(object):
    @cached_property
    def lazy_attribute(self):
        print('here')
        return 1


class TestUtils(unittest.TestCase):
    """
    Test utility functions

    Note: mock.patch has been used to mock warnings.warn rather than using the
    context manager to catch any warnings called. This is because there is no
    easy way to reset them, see:

    http://bugs.python.org/issue21724

    """

    def setUp(self):
        self.dc = DummyClass()
  
    @mock.patch('ads.utils.warnings')
    def test_cached_property(self, m_warn):
        """
        Test that the cached property raises a warning when __get__ is accessed
        """

        m_warn.warn.return_value = None

        # Lazy load should trigger message
        self.dc.lazy_attribute
        self.assertEqual(
            len(m_warn.warn.mock_calls),
            1
        )

        # Should only print once unless the filter is changed
        self.dc.lazy_attribute
        self.assertEqual(
            len(m_warn.warn.mock_calls),
            1
        )
        m_warn.warn.assert_called_once()

    @mock.patch('ads.utils.warnings')
    def test_cached_property_already_loaded(self, m_warn):
        """
        Test there is no warning message when someone accesses a lazy loading
        attribute that has already been loaded on instantiation.
        """

        # Pretend we have this value in our object already
        setattr(self.dc, 'lazy_attribute', 1)

        # Lazy load test
        self.assertEqual(
            len(m_warn.warn.mock_calls),
            0
        )

        self.dc.lazy_attribute

        self.assertEqual(
            len(m_warn.warn.mock_calls),
            0
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)
