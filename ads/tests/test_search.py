"""
Tests for the search interface
"""
import sys
import unittest
import requests
from mock import patch
import six
import warnings

from ads.tests.mocks import MockSolrResponse

from ads.search import SearchQuery, SolrResponse, APIResponse, Article, query
from ads.exceptions import APIResponseError, SolrResponseParseError
from ads.config import SEARCH_URL


class TestArticle(unittest.TestCase):
    """
    Test the Article object
    """

    def setUp(self):
        """
        Create a test Article instance
        """
        self.article = Article(
            bibcode="2013A&A...552A.143S",
            year=2013,
            first_author="Sudilovsky, V.",
            author=[
                "Sudilovsky, V",
                "Greiner, J",
                "Rau, A",
                "Salvato, M",
                "Savaglio, S",
                "Vergani, S",
                "Schady, P",
                "Elliott, J",
                "Kruehler, T",
                "Kann, D",
                "Klose, S",
                "Rossi, A",
                "Filgas, R",
                "Schmidl, S"
            ],
        )

    def test_equals(self):
        """
        the __eq__ method should compare bibcodes, and raise if bibcode isn't
        defined
        """
        self.assertNotEqual(Article(bibcode="Not the same"), self.article)
        self.assertEqual(Article(bibcode="2013A&A...552A.143S"), self.article)
        with self.assertRaises(TypeError):
            Article() == self.article

    def test_init(self):
        """
        after init ._raw should be a dict containing a subset of all
        class attributes
        """
        for key, value in six.iteritems(self.article._raw):
            self.assertEqual(
                self.article.__getattribute__(key),
                value,
                msg="Instance attribute and _raw mismatch on {}".format(key)
            )

    def test_print_methods(self):
        """
        the class should return a user-friendly formatted identified when the
        __str__ or __unicode__ methods are called
        """
        self.assertEqual(
            '<Sudilovsky, V. et al. 2013, 2013A&A...552A.143S>',
            self.article.__str__()
        )
        self.assertEqual(self.article.__unicode__(), self.article.__str__())

    @patch('ads.search.Article._get_field')
    def test_cached_properties(self, patched):
        """
        The underlying computation responsible for filling in cached properties
        should be called once and only once per attribute.
        In addition, this computation should only be called if the instance
        attribute wasn't set elsewhere.
        """
        patched.return_value = "patched response"
        # explicitly set attributes shouldn't be managed by cached_property
        self.article.year
        self.assertEqual(patched.call_count, 0)

        self.assertEqual(self.article.aff, 'patched response')
        self.assertEqual(self.article.aff, 'patched response')
        patched.assert_called_once_with('aff')
        self.assertEqual(patched.call_count, 1)

    def test_get_field(self):
        """
        The helper method _get_field() should return the value of a field
        based on its `id`
        """
        with self.assertRaisesRegexp(
                APIResponseError,
                "Cannot query an article without an id"):
            self.article._get_field('read_count')

        # Note that our mock solr server doesn't do anything with "q", and
        # therefore will just return the first article in the hardcoded
        # stubdata. We assume the live service will return the correct document.
        self.article.id = 9535116
        with MockSolrResponse(SEARCH_URL):
            self.assertEqual(self.article.pubdate, '1971-10-00')
            self.assertEqual(self.article.read_count, 0.0)
            self.assertIsNone(self.article.issue)


class TestSearchQuery(unittest.TestCase):
    """
    Tests for SearchQuery. Depends on SolrResponse.
    """

    def test_rows_rewrite(self):
        """
        if the responseHeader "rows" is not the same as the query's "rows",
        the query's "rows" should be re-written and a warning should be emitted
        """
        sq = SearchQuery(q="unittest", rows=10e6)
        with MockSolrResponse(sq.HTTP_ENDPOINT):
            self.assertEqual(sq.query['rows'], 10e6)
            with warnings.catch_warnings(record=True) as w:
                next(sq)
                if six.PY3:
                    msg = w[-1].message.args[0]
                elif six.PY2:
                    msg = w[-1].message.message
                self.assertEqual(
                    msg,
                    "Response rows did not match input rows. Setting this query's rows to 300"
                )
            self.assertEqual(sq.query['rows'], 300)

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
            self.assertEqual(len(list(sq)), 18)  # 2 already returned
            with self.assertRaisesRegexp(
                    StopIteration,
                    "Maximum number of pages queried"):
                next(sq)
            sq.max_pages = 500
            self.assertEqual(len(list(sq)), 28-18-2)
            with self.assertRaisesRegexp(
                    StopIteration,
                    "All records found"):
                next(sq)

        # not setting max_pages should return the exact number of rows requests
        sq = SearchQuery(q="unittest", rows=3)
        with MockSolrResponse(sq.HTTP_ENDPOINT):
            self.assertEqual(len(list(sq)), 3)

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

        sq = SearchQuery(q="q", token="test-token")
        self.assertEqual(sq.token, "test-token")
        self.assertEqual(sq._token, "test-token")


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
        self.assertEqual(sr.fl, ["id", "doi", "bibcode"])

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

    @patch('ads.search.Article._get_field')
    def test_default_article_fields(self, patched):
        """
        articles should have their properties set to None for each key in fl,
        if the response has no data.
        """
        sr = SolrResponse(self.response.text)
        sr.docs = [{"id": 1}]
        sr.fl = ['id', 'bibstem']
        self.assertEqual(sr.articles[0].id, 1)
        self.assertEqual(sr.articles[0].bibstem, None)
        self.assertEqual(patched.call_count, 0)



class Testquery(unittest.TestCase):
    """
    Test the to-be-deprecated "query" class
    """

    def test_init(self):
        """
        passing a :type str as the first argument to query.__init__() should
        create an instansiated SearchQuery whose "q" is that string
        """
        _ = query("star")
        self.assertEqual(_._query['q'], "star")
        _ = query({"q": "star"})
        self.assertEqual(_._query['q'], "star")
        self.assertIsInstance(_, SearchQuery)


if __name__ == '__main__':
    unittest.main(verbosity=2)
