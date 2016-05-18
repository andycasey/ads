"""
Tests for ExportQuery
"""
import unittest
import six
import os

from .mocks import MockResponse, MockExportResponse

from ads.export import ExportQuery, ExportResponse
from ads.config import EXPORT_URL


class TestMetricsQuery(unittest.TestCase):
    """
    test the ExportQuery object
    """

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


class TestExportResponse(unittest.TestCase):
    """
    test ExportResponse object
    """

    def test_init(self):
        """
        an initialized ExportResponse should have an attribute result
        that is a string, and an attribute _raw that is a string
        """
        er = ExportResponse(MockResponse('{"export": "[data]"}'))
        self.assertEqual(er.result, "[data]")  # No parsing!
        self.assertIsInstance(er._raw, six.string_types)

if __name__ == '__main__':
    unittest.main(verbosity=2)