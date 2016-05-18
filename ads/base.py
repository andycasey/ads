"""
Base classes for the ads client
"""

import requests
import warnings
import json
import os

from .exceptions import APIResponseError
from .config import TOKEN_FILES, TOKEN_ENVIRON_VARS
from . import __version__
import ads.config  # For manually setting the token


class _Singleton(type):
    _instances = {}

    def __call__(cls, name, *args, **kwargs):
        if name not in cls._instances:
            cls._instances[name] = super(_Singleton, cls).__call__(name, *args, **kwargs)
        return cls._instances[name]

    @classmethod
    def get_info(cls):
        """
        Print all of the instantiated Singletons
        """
        return '\n'.join(
            [str(cls._instances[key]) for key in cls._instances]
        )


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    """
    Wrapper class so that the Singleton metaclass works for both Python 2&3
    """
    pass


class RateLimits(Singleton):
    response_to_query = {
            'SolrResponse': 'SearchQuery',
            'MetricsResponse': 'MetricsQuery',
            'ExportResponse': 'ExportQuery'
        }

    def __init__(self, name):
        self.limits = {}
        self.name = self.response_to_query.get(name, name)

    @classmethod
    def getRateLimits(cls, name):
        return cls(cls.response_to_query.get(name, name))

    def set(self, headers):
        self.limits = {
            'limit': headers.get('x-ratelimit-limit', ''),
            'remaining': headers.get('x-ratelimit-remaining', ''),
            'reset': headers.get('x-ratelimit-reset', '')
        }

    def to_dict(self):
        return self.limits

    def __str__(self):
        return '{}: {}'.format(
            self.name,
            json.dumps(self.limits)
        )


class APIResponse(object):
    """
    Represents an adsws-api http response
    """
    response = None

    @classmethod
    def get_ratelimits(cls):
        """
        Return the current, maximum, and reset rate limits from the response
        header as a dictionary. The values will be strings.
        """
        return RateLimits.getRateLimits(cls.__name__).to_dict()

    @classmethod
    def load_http_response(cls, http_response):
        """
        This method should return an instantiated class and set its response
        to the requests.Response object.
        """
        if not http_response.ok:
            raise APIResponseError(http_response.text)
        c = cls(http_response)
        c.response = http_response

        RateLimits.getRateLimits(cls.__name__).set(c.response.headers)

        return c


class BaseQuery(object):
    """
    Represents an arbitrary query to the adsws-api
    """
    _session = None
    _token = ads.config.token

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
        Each subclass should define their own execute method
        """
        raise NotImplementedError
