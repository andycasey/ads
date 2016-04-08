"""
Tests for utility functions
"""
import os
import unittest

from .mocks import MockMetricsResponse, MockSolrResponse, MockExportResponse

from ads.utils import get_ratelimits
from ads.metrics import MetricsQuery
from ads.search import SearchQuery
from ads.export import ExportQuery
from ads.config import METRICS_URL, SEARCH_URL, EXPORT_URL


class TestUtilities(unittest.TestCase):
    """
    Test the utility functions
    """
    def setUp(self):
        """
        Reset rate limits
        """
        for query in [MockSolrResponse, MockMetricsResponse, MockExportResponse]:
            query.current_ratelimit = 400
        for query in [MetricsQuery, SearchQuery, ExportQuery]:
            query._response = None

    def test_get_ratelimit(self):
        """
        Test the pretty printing of get_ratelimit()
        """
        # First everything should be None
        ratelimits = get_ratelimits()
        self.assertEqual(
            ratelimits['/export']['remaining'], None
        )
        self.assertEqual(
            ratelimits['/metrics']['remaining'], None
        )
        self.assertEqual(
            ratelimits['/search']['remaining'], None
        )

        # Now we can get some fake rates for
        # /search
        q = SearchQuery(q="unittest", rows=1, max_pages=20)
        with MockSolrResponse(SEARCH_URL):
            q.execute()
        ratelimits = get_ratelimits()
        self.assertEqual(
            ratelimits['/export']['remaining'], None
        )
        self.assertEqual(
            ratelimits['/metrics']['remaining'], None
        )
        self.assertEqual(
            ratelimits['/search']['remaining'], '399'
        )

        # /metrics
        m = MetricsQuery('bibcode')
        with MockMetricsResponse(METRICS_URL):
            m.execute()
        ratelimits = get_ratelimits()
        self.assertEqual(
            ratelimits['/export']['remaining'], None
        )
        self.assertEqual(
            ratelimits['/metrics']['remaining'], '399'
        )
        self.assertEqual(
            ratelimits['/search']['remaining'], '399'
        )

        # /export
        e = ExportQuery('bibcode')
        with MockExportResponse(os.path.join(EXPORT_URL, "bibtex")):
            e.execute()
        ratelimits = get_ratelimits()
        self.assertEqual(
            ratelimits['/export']['remaining'], '399'
        )
        self.assertEqual(
            ratelimits['/metrics']['remaining'], '399'
        )
        self.assertEqual(
            ratelimits['/search']['remaining'], '399'
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)