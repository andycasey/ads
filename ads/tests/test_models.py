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
    def test_init(self):
        """
        ensure that an init of SolrResponse has the expected keys,
        and that if critical data are missing then raise SolrResponseParseError
        """

        # Load stubdata via a http workflow
        with MockSolrResponse('http://solr-response.unittest'):
            response = requests.get('http://solr-response.unittest')

        sr = SolrResponse(response.text)
        self.assertIn('responseHeader', sr.json)
        self.assertIn('response', sr.json)
        self.assertEqual(sr.numFound, 1)

        malformed_text = response.text.replace(
            'responseHeader',
            'this_is_now_malformed_data',
        )
        with self.assertRaises(SolrResponseParseError):
            SolrResponse(malformed_text)

    def test_load_http_response(self):
        """
        the classmethod load_http_response() should return an instansiated
        SolrResponse class that has an .articles attribute that are Article
        objects

        this test also excersices the @articles property
        """

        # Load stubdata via a http workflow
        with MockSolrResponse('http://solr-response.unittest'):
            response = requests.get('http://solr-response.unittest')

        sr = SolrResponse.load_http_response(response)
        self.assertEquals(len(sr.articles), 1)
        self.assertIsInstance(sr.articles[0], Article)
        self.assertEqual(sr.articles[0].doi, [u'10.1051/0004-6361/201321247'])


class TestArticle(unittest.TestCase):
    """
    Test the Article object
    """

    def setUp(self):
        """
        Set up this test by loading stub data via the SolrResponse class using
        an http interface --> dependency on ads.models.SolrResponse
        """
        with MockSolrResponse('http://solr-response.unittest'):
            response = requests.get('http://solr-response.unittest')
        self.article = SolrResponse.load_http_response(response).articles[0]

    def test_init(self):
        """
        after init, the attributes _references and _citations should be None,
        _raw should be equal to
        """
        pass