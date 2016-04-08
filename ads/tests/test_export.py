"""
Tests for ExportQuery
"""
import unittest
import six
import os

from .mocks import MockExportResponse

from ads.export import ExportQuery, ExportResponse
from ads.config import EXPORT_URL


class TestMetricsQuery(unittest.TestCase):
    """
    test the ExportQuery object
    """
    def setUp(self):
        """
        Clear rate limits
        """
        MockExportResponse.current_ratelimit = 400

    def test_init(self):
        """
        an initialized ExportQuery object should have a bibcode attributes
        that is a list
        """
        self.assertEqual(ExportQuery('bibcode').bibcodes, ['bibcode'])
        self.assertEqual(ExportQuery(['b1', 'b2']).bibcodes, ['b1', 'b2'])

    def test_execute(self):
        """
        ExportQuery.execute() should return a ExportResponse object, and
        that object should be set as the .response attribute
        """
        eq = ExportQuery('bibcode')
        with MockExportResponse(os.path.join(EXPORT_URL, "bibtex")):
            retval = eq.execute()
        self.assertIsInstance(eq.response, ExportResponse)
        self.assertEqual(retval, eq.response.result)

    def test_ratelimit_on_cached_property_access(self):
        """
        When a cached property is accessed, the parent query object should
        update the rate limit appropriately.
        """
        export_query = ExportQuery('bibcode')
        with MockExportResponse(os.path.join(EXPORT_URL, "bibtex")):
            export_query.execute()

        self.assertEqual(export_query.get_ratelimits(), {'reset': '1436313600', 'limit': '400', 'remaining': '399'})
        self.assertEqual(ExportQuery.get_ratelimits(), {'reset': '1436313600', 'limit': '400', 'remaining': '399'})


class TestExportResponse(unittest.TestCase):
    """
    test ExportResponse object
    """

    def test_init(self):
        """
        an initialized ExportResponse should have an attribute result
        that is a string, and an attribute _raw that is a string
        """
        er = ExportResponse('{"export": "[data]"}')
        self.assertEqual(er.result, "[data]")  # No parsing!
        self.assertIsInstance(er._raw, six.string_types)

if __name__ == '__main__':
    unittest.main(verbosity=2)