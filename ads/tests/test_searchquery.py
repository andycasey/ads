"""
Tests for SearchQuery and it's query proxy class.
"""
import sys
import unittest

from mocks import MockSolrResponse

from ads.core import SearchQuery, query


class TestSearchQuery(unittest.TestCase):
    """
    Tests for SearchQuery. Depends on SolrResponse.
    """

    def test_iter(self):
        """
        the iteration method should handle pagination automatically
        based on rows and max_rows; use the mock solr server to query
        data row by row and ensure that the data return as expected
        """

        sq = SearchQuery(q="unittest", rows=1, max_pages=20)
        with MockSolrResponse(sq.HTTP_ENDPOINT):
            self.assertEqual(sq._query['start'], 0)
            self.assertEqual(next(sq).bibcode, '1971Sci...174..142S')
            self.assertEqual(len(sq.articles), 1)
            self.assertEqual(sq._query['start'], 1)
            self.assertEqual(next(sq).bibcode, '2012GCN..13229...1S')
            self.assertEqual(len(list(sq)), 19)  # 2 already returned
            with self.assertRaisesRegexp(
                    StopIteration,
                    "Maximum number of pages queried"):
                next(sq)
            sq.max_pages = 500
            self.assertEqual(len(list(sq)), 28-19-2)
            with self.assertRaisesRegexp(
                    StopIteration,
                    "All records found"):
                next(sq)

    def test_init(self):
        """
        init should result in a properly formatted query attribute
        """

        with self.assertRaisesRegexp(AssertionError, "q must not be empty"):
            SearchQuery()

        sq = SearchQuery(q="star")
        self.assertIn("star", sq.query['q'])

        sq = SearchQuery(title="t", author="ln, fn")

        # In Python 3, assertItemsEqual is named assertCountEqual
        assertItemsEqual = self.assertItemsEqual if sys.version_info[0] == 2 \
            else self.assertCountEqual
        
        assertItemsEqual(
            sq.query['q'].split(),
            'title:"t" author:"ln, fn"'.split(),
        )

        sq = SearchQuery(q="star", aff="institute")
        assertItemsEqual(
            sq.query['q'].split(),
            'aff:"institute" star'.split(),
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)
