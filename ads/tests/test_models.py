"""
Test that classes for representing the adsws-api specific data structures
defined in models.py
"""
import unittest

from ads.models import SolrResponse, Article
from ads.exceptions import SolrResponseParseError

import requests
from mocks import MockSolrResponse


class TestSolrResponse(unittest.TestCase):
    """
    Test the SolrResponse object
    """
    def setUp(self):
        """
        setup this test with a mocked solr response via http
        """
        with MockSolrResponse('http://solr-response.unittest'):
            self.response = requests.get('http://solr-response.unittest')

    def test_init(self):
        """
        ensure that an init of SolrResponse has the expected keys,
        and that if critical data are missing then raise SolrResponseParseError
        """

        sr = SolrResponse(self.response.text)
        self.assertIn('responseHeader', sr.json)
        self.assertIn('response', sr.json)
        self.assertEqual(sr.numFound, 1)

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
        self.assertEqual(len(sr.articles), 1)
        self.assertEqual(sr._articles, sr.articles)
        with self.assertRaises(AttributeError):
            sr.articles = 'this should be read-only'

    def test_load_http_response(self):
        """
        the classmethod load_http_response() should return an instansiated
        SolrResponse class that has an .articles attribute that are Article
        objects
        """
        sr = SolrResponse.load_http_response(self.response)
        self.assertEquals(len(sr.articles), 1)
        self.assertIsInstance(sr.articles[0], Article)
        self.assertEqual(sr.articles[0].doi, [u'10.1051/0004-6361/201321247'])


class TestArticle(unittest.TestCase):
    """
    Test the Article object
    """

    def setUp(self):
        """
        Set up these tests by loading stub data via the SolrResponse class
        using an http interface --> dependency on ads.models.SolrResponse
        """
        with MockSolrResponse('http://solr-response.unittest'):
            response = requests.get('http://solr-response.unittest')
        self.article = SolrResponse.load_http_response(response).articles[0]

    def test_init(self):
        """
        after init, the attributes _references and _citations should be None,
        _raw should be a dict containing a subset of all class attributes
        """
        self.assertIsNone(self.article._references)
        self.assertIsNone(self.article._citations)
        self.assertIsNone(self.article._bibtex)
        for key, value in self.article._raw.iteritems():
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




if __name__ == '__main__':
    unittest.main(verbosity=2)
