"""
Tests for SearchQuery and it's query proxy class.
"""
import sys
import unittest
import requests

from .mocks import MockSolrResponse

from ads.core import SearchQuery, query, SolrResponse, APIResponse
from ads.exceptions import APIResponseError, SolrResponseParseError


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


class TestSolrResponse(unittest.TestCase):
    """
    Test the SolrResponse object
    """
    def setUp(self):
        """
        setup this test with a mocked solr response via http
        """
        with MockSolrResponse('http://solr-response.unittest'):
            self.response = requests.get(
                'http://solr-response.unittest',
                params={'fl': ["id", "doi", "bibcode"]}
            )

    def test_init(self):
        """
        ensure that an init of SolrResponse has the expected keys,
        and that if critical data are missing then raise SolrResponseParseError
        """

        sr = SolrResponse(self.response.text)
        self.assertIn('responseHeader', sr.json)
        self.assertIn('response', sr.json)
        self.assertEqual(sr.numFound, 28)

        malformed_text = self.response.text.replace(
            'responseHeader',
            'this_is_now_malformed_data',
        )
        with self.assertRaises(SolrResponseParseError):
            SolrResponse(malformed_text)

    def test_articles(self):
        """
        the article attribute should be read-only, and set the first time
        it is called
        """
        sr = SolrResponse(self.response.text)
        self.assertIsNone(sr._articles)
        self.assertEqual(len(sr.articles), 28)
        self.assertEqual(sr._articles, sr.articles)
        self.assertEqual(sr.articles[0].doi, [u'10.1126/science.174.4005.142'])
        with self.assertRaises(AttributeError):
            sr.articles = 'this should be read-only'

    def test_load_http_response(self):
        """
        the classmethod load_http_response() should return an instansiated
        SolrResponse class
        """
        sr = SolrResponse.load_http_response(self.response)
        self.assertIsInstance(sr, SolrResponse)
        self.assertIsInstance(sr, APIResponse)
        self.assertEqual(sr.response, self.response)

        # Response with a non-200 return code should raise
        self.response.status_code = 500
        with self.assertRaises(APIResponseError):
            SolrResponse.load_http_response(self.response)



if __name__ == '__main__':
    unittest.main(verbosity=2)
