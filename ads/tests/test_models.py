"""
Test that classes for representing the adsws-api specific data structures
defined in core.py
"""
import unittest

import ads.core
from ads.core import SolrResponse, Article, BaseQuery, APIResponse
from ads.exceptions import SolrResponseParseError, SolrResponseError
from .mocks import MockSolrResponse, MockApiResponse
from ads.config import SEARCH_URL

from mock import patch
import requests
import os
import six

from tempfile import NamedTemporaryFile


class TestApiResponse(unittest.TestCase):
    """
    test the base Api response class
    """
    def setUp(self):
        with MockApiResponse('http://api.unittest'):
            self.APIResponse = APIResponse()
            self.APIResponse.response = requests.get('http://api.unittest')

    def test_get_ratelimits(self):
        """
        the get_ratelimit method should return the X-RateLimit headers in
        a dictionary
        """
        limits = self.APIResponse.get_ratelimits()
        self.assertEqual(limits['limit'], '400')
        self.assertEqual(limits['remaining'], '397')
        self.assertEqual(limits['reset'], '1436313600')


class TestBaseQuery(unittest.TestCase):
    """
    Test the BaseQuery object
    """
    def test_token(self):
        """
        the token should be set in the following order:
        (first in list) environmental variables defined in TOKEN_ENVIRON_VARS
        (first in list) files on disk defined in TOKEN_FILES
        """
        def reset_token():
            bq.token = None

        # In-place override of the config variables responsible for identifying
        # how to look for a token
        ads.core.TOKEN_ENVIRON_VARS = ['TOKEN_1', 'TOKEN_2']
        os.environ['TOKEN_1'] = "tok1"
        os.environ['TOKEN_2'] = "tok2"

        # Write temporary file and override the config variable with the
        # tempfile paths
        tf1, tf2 = NamedTemporaryFile(), NamedTemporaryFile()
        tf1.write('tok3\n'.encode("utf-8"))
        tf2.write(' tok4 '.encode("utf-8"))
        [f.flush() for f in [tf1, tf2]]
        [f.seek(0) for f in [tf1, tf2]]
        ads.core.TOKEN_FILES = [tf1.name, tf2.name]

        bq = BaseQuery()

        self.assertEqual(bq.token, 'tok1')
        reset_token()
        del os.environ['TOKEN_1']

        self.assertEqual(bq.token, 'tok2')
        reset_token()
        del os.environ['TOKEN_2']

        self.assertEqual(bq.token, 'tok3')
        reset_token()
        tf1.close()

        self.assertEqual(bq.token, 'tok4')
        reset_token()
        tf2.close()

        self.assertEqual(bq.token, None)


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
        with self.assertRaises(SolrResponseError):
            SolrResponse.load_http_response(self.response)



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

    @patch('ads.core.Article._get_field')
    def test_cached_properties(self, patched):
        """
        The underlying computation responsible for filling in cached properties
        should be called once and only once per attribute.
        In addition, this computation should only be called if the instance
        attribute wasn't set elsewhere.
        """
        patched.return_value = "patched response"
        self.assertEqual(self.article.bibcode, '2013A&A...552A.143S')
        self.assertEqual(self.article.aff, 'patched response')
        self.assertEqual(self.article.aff, 'patched response')
        patched.assert_called_once_with('aff')

    def test_get_field(self):
        """
        The helper method _get_field() should return the value of a field
        based on its `id`
        """
        with self.assertRaisesRegexp(
                SolrResponseError,
                "Cannot query an article without an id"):
            self.article._get_field('read_count')

        # Note that our mock solr server doesn't do anything with "q", and
        # therefore will just return the first article in the hardcoded
        # stubdata. We assume the live service will return the correct document.
        self.article.id = 9535116
        with MockSolrResponse(SEARCH_URL):
            self.assertEqual(self.article.pubdate, '1971-10-00')
            self.assertEqual(self.article.read_count, 0.0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
