"""
Test that classes for representing the adsws-api specific data structures
defined in core.py
"""
import json
import unittest
import requests
import os
from tempfile import NamedTemporaryFile

import ads.base
import ads.config
from ads.base import BaseQuery, APIResponse, RateLimits, _Singleton
from .mocks import MockApiResponse


@unittest.skip('deprecated by RateLimits class')
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
        - (first in list) environmental variables defined in TOKEN_ENVIRON_VARS
        - (first in list) files on disk defined in TOKEN_FILES
        - ads.config.token
        """
        def reset_token():
            bq.token = None

        # In-place override of the config variables responsible for identifying
        # how to look for a token
        ads.base.TOKEN_ENVIRON_VARS = ['TOKEN_1', 'TOKEN_2']
        os.environ['TOKEN_1'] = "tok1"
        os.environ['TOKEN_2'] = "tok2"

        # Write temporary file and override the config variable with the
        # tempfile paths
        tf1, tf2 = NamedTemporaryFile(delete=False), NamedTemporaryFile(delete=False)
        tf1.write('tok3\n'.encode("utf-8"))
        tf2.write(' tok4 '.encode("utf-8"))
        [f.close() for f in [tf1, tf2]]
        ads.base.TOKEN_FILES = [tf1.name, tf2.name]

        bq = BaseQuery()

        self.assertEqual(bq.token, 'tok1')
        reset_token()
        del os.environ['TOKEN_1']

        self.assertEqual(bq.token, 'tok2')
        reset_token()
        del os.environ['TOKEN_2']

        self.assertEqual(bq.token, 'tok3')
        reset_token()
        os.remove(tf1.name)

        self.assertEqual(bq.token, 'tok4')
        reset_token()
        os.remove(tf2.name)

        self.assertEqual(bq.token, None)

        ads.config.token = "tok5"
        self.assertEqual(BaseQuery().token, "tok5")

    def test_headers(self):
        """
        basequery's session object should have pre-defined headers
        """
        hdrs = BaseQuery().session.headers
        self.assertEqual(hdrs['Content-Type'], 'application/json')
        self.assertIn('ads-api-client', hdrs['User-Agent'])
        self.assertIn('Bearer', hdrs['Authorization'])


class TestRateLimits(unittest.TestCase):
    """
    Test rate limits
    """

    def setUp(self):
        class FakeResponse(APIResponse):
            def __init__(self, http_response):
                pass

        self.FakeResponse = FakeResponse
        _Singleton._instances = {}

        MockApiResponse.remaining = 398

    def test_get_ratelimits(self):
        """
        Test the two ways in which someone can access the rate limits via
        the RateLimit singleton class. Via an instantiation of the relevant
        query class, or the response object.
        """

        with MockApiResponse('http://api.unittest'):
            r1 = self.FakeResponse.load_http_response(
                requests.get('http://api.unittest')
            )

        # Via the singleton
        limits = RateLimits('FakeResponse').to_dict()
        self.assertEqual(limits['limit'], '400')
        self.assertEqual(limits['remaining'], '397')
        self.assertEqual(limits['reset'], '1436313600')

        # Via the response object
        limits = r1.get_ratelimits()
        self.assertEqual(limits['limit'], '400')
        self.assertEqual(limits['remaining'], '397')
        self.assertEqual(limits['reset'], '1436313600')

        with MockApiResponse('http://api.unittest'):
            r2 = self.FakeResponse.load_http_response(
                requests.get('http://api.unittest')
            )

        # Check all response objects get most up-to-date information
        limits = r1.get_ratelimits()
        self.assertEqual(limits['limit'], '400')
        self.assertEqual(limits['remaining'], '396')
        self.assertEqual(limits['reset'], '1436313600')

        self.assertEqual(
            r1.get_ratelimits(),
            r2.get_ratelimits()
        )

        self.assertEqual(
            r1.get_ratelimits(),
            RateLimits('FakeResponse').to_dict()
        )

    def test_singleton(self):
        """
        Test singleton behaves as expected
        """
        sq1 = RateLimits('SolrResponse')
        sq2 = RateLimits('SolrResponse')

        self.assertEqual(id(sq1), id(sq2))

        mq = RateLimits('MetricsResponse')
        self.assertNotEqual(id(sq1), id(mq))

    def test_pretty_print(self):
        """
        Test pretty print
        """
        RateLimits.response_to_query['FakeResponse'] = 'FakeQuery'

        with MockApiResponse('http://api.unittest'):
            self.FakeResponse.load_http_response(
                requests.get('http://api.unittest')
            )

        message = RateLimits.get_info()
        self.assertIn('FakeQuery', message)
        self.assertEqual(
            {"reset": "1436313600", "limit": "400", "remaining": "397"},
            json.loads(message.split('FakeQuery: ')[1])
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
