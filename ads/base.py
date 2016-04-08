"""
Base classes for the ads client
"""

import requests
import warnings
import os
import re

from .exceptions import APIResponseError
from .config import TOKEN_FILES, TOKEN_ENVIRON_VARS
from . import __version__
import ads.config  # For manually setting the token


class APIResponse(object):
    """
    Represents an adsws-api http response
    """
    response = None

    def get_ratelimits(self):
        """
        Return the current, maximum, and reset rate limits from the response
        header as a dictionary. The values will be strings.
        """
        return {
            "limit": self.response.headers.get('X-RateLimit-Limit'),
            "remaining": self.response.headers.get('X-RateLimit-Remaining'),
            "reset": self.response.headers.get('X-RateLimit-Reset')
            }

    @classmethod
    def load_http_response(cls, HTTPResponse, parent=None):
        """
        This method should return an instansitated class and set its response
        to the requests.Response object.
        """
        if not HTTPResponse.ok:
            raise APIResponseError(HTTPResponse.text)
        c = cls(HTTPResponse.text)
        c.response = HTTPResponse
        c._parent = parent
        return c


class BaseQuery(object):
    """
    Represents an arbitrary query to the adsws-api
    """
    _session = None
    _token = ads.config.token
    _response = None
    _name = None
    HTTP_ENDPOINT = None
    MockResponse = None

    def __init__(self, test=False):
        self._request_count = {}
        self._test = test

    def increment_request(self, name=None):
        """
        Incremement the number of requests and update a dictionary for storage
        of the information

        :param name: name of the service being contacted
        :type name: str
        """
        _name = name if name else self._name
        self._request_count.setdefault(_name, dict(test_requests=0, requests=0))
        if self._test:
            self._request_count[_name]['test_requests'] += 1
        else:
            self._request_count[_name]['requests'] += 1

    def get_request_stats(self):
        """
        Return the request statistics
        :return: dict
        """
        return self._request_count

    @classmethod
    def get_ratelimits(cls):
        """
        Rate limit of the current query object, which is held by its associated
        APIResponse object.
        """
        if cls._response:
            return cls._response.get_ratelimits()
        else:
            return {'reset': None, 'limit': None, 'remaining': None}

    @property
    def token(self):
        """
        set the instance attribute `token` following the following logic,
        stopping whenever a token is found. Raises NoTokenFound is no token
        is found
        - environment variables TOKEN_ENVIRON_VARS
        - file containing plaintext as the contents in TOKEN_FILES
        - ads.config.token
        """
        if self._token is None:
            for v in map(os.environ.get, TOKEN_ENVIRON_VARS):
                if v is not None:
                    self._token = v
                    return self._token
            for f in TOKEN_FILES:
                try:
                    with open(f) as fp:
                        self._token = fp.read().strip()
                        return self._token
                except IOError:
                    pass
            if ads.config.token is not None:
                self._token = ads.config.token
                return self._token
            warnings.warn("No token found", RuntimeWarning)
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    @property
    def session(self):
        """
        http session interface, transparent proxy to requests.session
        """
        if self._session is None:
            self._session = requests.session()
            self._session.headers.update(
                {
                    "Authorization": "Bearer {}".format(self.token),
                    "User-Agent": "ads-api-client/{}".format(__version__),
                    "Content-Type": "application/json",
                }
            )
        return self._session

    def __call__(self):
        return self.execute()

    def execute(self):
        """
        Wrapper for _execute
        """
        if self._test:
            if self.MockResponse is None or self.HTTP_ENDPOINT is None:
                raise NotImplementedError

            with self.MockResponse(re.compile(self.HTTP_ENDPOINT)):
                r = self._execute()
        else:
            r = self._execute()

        self.increment_request(name=self._name)
        return r

    def _execute(self):
        """
        Each subclass should define their own execute method
        """
        raise NotImplementedError
