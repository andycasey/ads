"""
Test that classes for representing the adsws-api specific data structures
defined in core.py
"""
import unittest
import requests
import os
from tempfile import NamedTemporaryFile

import ads.base
import ads.config
from ads.base import BaseQuery, APIResponse
from .mocks import MockApiResponse


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
        tf1, tf2 = NamedTemporaryFile(), NamedTemporaryFile()
        tf1.write('tok3\n'.encode("utf-8"))
        tf2.write(' tok4 '.encode("utf-8"))
        [f.flush() for f in [tf1, tf2]]
        [f.seek(0) for f in [tf1, tf2]]
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
        tf1.close()

        self.assertEqual(bq.token, 'tok4')
        reset_token()
        tf2.close()

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

    def test_rate_limit(self):
        """
        Test rate limit property
        """
        base_query = BaseQuery()
        api_response = APIResponse()
        BaseQuery._response = api_response

        with MockApiResponse('http://api.unittest'):
            APIResponse.response = requests.get('http://api.unittest')

        self.assertEqual(base_query.get_ratelimits(), {'reset': '1436313600', 'limit': '400', 'remaining': '397'})

        base_query = BaseQuery()
        self.assertEqual(base_query.get_ratelimits(), {'reset': '1436313600', 'limit': '400', 'remaining': '397'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
