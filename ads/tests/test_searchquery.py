"""
Tests for SearchQuery and it's query proxy class.
"""
import unittest

from mocks import MockSolrResponse

from ads.core import SearchQuery, query


class TestSearchQuery(unittest.TestCase):
    """
    Tests for SearchQuery. Depends on SolrResponse.
    """

    def test_iter(self):
        """
        the iteration method
        """

        sq = SearchQuery(q="unittest", rows=1, max_pages=20)
        with MockSolrResponse(sq.api_endpoint):
            self.assertEqual(sq._query['start'], 0)
            self.assertEqual(next(sq).bibcode, '1971Sci...174..142S')
            self.assertEqual(len(sq.articles), 1)
            self.assertEqual(sq._query['start'], 1)
            self.assertEqual(next(sq).bibcode, '2012GCN..13229...1S')
            self.assertEqual(len(list(sq)), 19)  # 2 already returned



if __name__ == '__main__':
    unittest.main(verbosity=2)
