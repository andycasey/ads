
import os
import unittest
import requests
import warnings
from tempfile import NamedTemporaryFile

from ads.tests.mocks import MockApiResponse

import ads

class TestBaseSession(unittest.TestCase):

    def setUp(self):
        self._token = ads.config.token
        self._token_environ_vars = [] + ads.config.TOKEN_ENVIRON_VARS
        self._token_files = [] + ads.config.TOKEN_FILES

    def tearDown(self):
        """ Remove any temporary tokens set. """
        ads.config.token = self._token
        ads.config.TOKEN_FILES = [] + self._token_files
        ads.config.TOKEN_ENVIRON_VARS = [] + self._token_environ_vars
        for key in ("TOKEN_1", "TOKEN_2"):
            if key in os.environ:
                del os.environ[key]


    def test_token(self):
        """
        Token is set in the following order:
        - (first in list) environmental variables defined in TOKEN_ENVIRON_VARS
        - (first in list) files on disk defined in TOKEN_FILES
        - ads.config.token
        """
        ads.config.TOKEN_ENVIRON_VARS = ['TOKEN_1', 'TOKEN_2']
        os.environ["TOKEN_1"] = "tok1"
        os.environ["TOKEN_2"] = "tok2"
        
        # Write temporary file and override the config variable with the
        # tempfile paths
        tf1, tf2 = NamedTemporaryFile(delete=False), NamedTemporaryFile(delete=False)
        tf1.write('tok3\n'.encode("utf-8"))
        tf2.write(' tok4 '.encode("utf-8"))
        [f.close() for f in [tf1, tf2]]
        ads.config.TOKEN_FILES = [tf1.name, tf2.name]

        client = ads.client.Client()

        self.assertEqual(client.token, "tok1")
        client.token = None
        del os.environ["TOKEN_1"]

        self.assertEqual(client.token, "tok2")
        client.token = None
        del os.environ["TOKEN_2"]

        self.assertEqual(client.token, "tok3")
        client.token = None
        os.remove(tf1.name)

        self.assertEqual(client.token, "tok4")
        client.token = None
        os.remove(tf2.name)

        # Check that a warning is emitted about the token being None.
        with warnings.catch_warnings(record=True) as w:
            self.assertEqual(client.token, None)
            self.assertEqual(len(w), 1)
            self.assertTrue(str(w[0].message).startswith("No SAO/NASA ADS API token found."))

        ads.config.token = "tok5"
        with ads.client.Client() as client:
            self.assertEqual(client.token, "tok5")
        
        # If an environment variable is set, that takes precedence over ads.config.token
        os.environ["TOKEN_1"] = "tok1"
        with ads.client.Client() as client:
            self.assertEqual(ads.config.token, "tok5")
            self.assertEqual(client.token, "tok1")        

    def test_headers(self):
        """ Check the request headers. """
        with ads.client.Client() as client:
            self.assertIn("ads-api-client", client.request_headers["User-Agent"])
            self.assertIn("Bearer", client.request_headers["Authorization"])
            self.assertEqual("application/json", client.request_headers["Content-Type"])
    

    def test_context_manager(self):
        with ads.client.Client() as client:
            self.assertTrue(client.session is not None)



class TestRateLimits(unittest.TestCase):

    start_remaining = 398

    def setUp(self):
        class FakeApiResponse(ads.client.APIResponse):
            def __init__(self, http_response):
                pass

        self.FakeApiResponse = FakeApiResponse

        MockApiResponse.remaining = self.start_remaining


    def test_rate_limits(self):
        for i in (1, 2):
            with MockApiResponse("http://api.unittest"):
                ads.client.RateLimits().set_from_http_response(
                    requests.get("http://api.unittest")
                )

            limits = ads.client.RateLimits().to_dict()
            self.assertEqual(limits[""]["limit"], 400)
            self.assertEqual(limits[""]["remaining"], self.start_remaining - i)
            self.assertEqual(limits[""]["reset"], 1436313600)
            

