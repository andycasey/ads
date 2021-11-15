import aiohttp
import asyncio
import os
import json
import requests
import warnings

from ads import logger, config
from .exceptions import APIResponseError

#from ads import config
#from ads import __version__
__version__ = "0.2.0" # TODO

TOKEN_FILES = list(map(os.path.expanduser,
    [
        "~/.ads/token",
        "~/.ads/dev_key",
    ]
))
TOKEN_ENVIRON_VARS = ["ADS_API_TOKEN", "ADS_DEV_KEY"]




class BaseQuery(object):

    _token = None #config.token # TODO
    _limit_per_host = 10
        
    @property
    def token(self):
        """
        Return the instance attribute `token` following the following logic,
        stopping whenever a token is found:

        - The environment variables in `TOKEN_ENVIRON_VARS`
        - File containing plaintext as the contents in `TOKEN_FILES`
        - `ads.config.token`
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
            # TODO: Allow this.
            #if ads.config.token is not None:
            #    self._token = ads.config.token
            #    return self._token
            warnings.warn("No token found", RuntimeWarning)
        return self._token


    @token.setter
    def token(self, value):
        self._token = value


    @property
    def request_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": f"ads-api-client/{__version__}",
            "Content-Type": "application/json"
        }


    @property
    def async_session(self):
        """ A client session for performing asynchronous HTTP requests. """
        while True:
            try:
                return self._async_session
            except AttributeError:
                # We are going to be good samaratins and limit the number of simultaneous connections.
                # (If we don't, ADS will do it anyways.)
                self._async_session = aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(limit_per_host=self._limit_per_host),
                    headers=self.request_headers
                )


    @property
    def session(self):
        """ A client session for performing synchronous HTTP requests. """
        while True:
            try:
                return self._session
            except AttributeError:
                self._session = requests.session()
                self._session.headers.update(self.request_headers)


    # Synchronous context manager.

    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        try:
            self.session.close()
        finally:
            return None

    
    def api_request(self, end_point, method="GET", **kwargs):
        """
        Perform a synchronous API request.
        
        :param end_point:
            The API end-point (e.g., '/search/query').
                
        :param method: [optional]
            The HTTP method to use for the request (default: GET).

        :param kwargs: [optional]
            Keyword arguments to pass to the `requests.request` method.
            Examples include `data`, `params`, etc.

        :returns:
            An `APIResponse` object.
        """

        url = self._api_url(end_point)
        available_methods = ("get", "post", "put", "delete")
        cleaned_method = method.lower().strip()
        if cleaned_method not in available_methods:
            raise ValueError(f"Method '{method}' not available. Available methods: {', '.join(available_methods)}")
        method_func = getattr(self.session, cleaned_method)

        return APIResponse.load_http_response(method_func(url, **kwargs))


    def _api_url(self, end_point):
        return "/".join(map(lambda _: _.strip("/"), [config.ADSWS_API_URL, end_point]))


    async def async_api_request(self, end_point, params, method="GET", **kwargs):
        
        raise NotImplementedError("todo")
        url = self._api_url(end_point)

        try:
            logger.info(f"Querying {url} with {params}")
            async with self.async_session.get(url, params=params) as response:
                logger.info(f"\tawaiting response on {params}")
                data = await response.json()
                logger.info(f"Retrieved response from {url} with {params}")
            return data

        except asyncio.CancelledError:
            logger.info(f"Cancelled request to {url} with {params}")
            raise


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]



class RateLimits(object, metaclass=Singleton):

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


    def set(self, response):
        self.limits.update({
            'limit': response.headers.get('x-ratelimit-limit', ''),
            'remaining': response.headers.get('x-ratelimit-remaining', ''),
            'reset': response.headers.get('x-ratelimit-reset', ''),
        })
        # TODO: Does this apply to ExportQuery and MetricsQuery?
        #if "max_rows" not in self.limits and has_multiple_pages(response):
        #    self.limits["max_rows"] = response.json()["responseHeader"]["para"]
        

    def to_dict(self):
        return self.limits

    def __str__(self):
        return '{}: {}'.format(
            self.name,
            json.dumps(self.limits)
        )


def has_multiple_pages(response):
    data = response.json()
    num_found = data["response"]["numFound"]
    start = data["response"]["start"]
    rows = data["responseHeader"]["params"]["rows"]
    if (num_found - start) > rows:
        return True
    return False


    



class APIResponse(object):
    """
    A response from an ADS API end point.
    
    """
    response = None

    @classmethod
    def load_http_response(cls, http_response):

        if not http_response.ok:
            try:
                raise APIResponseError(http_response.json()["error"])
            except (KeyError, AttributeError, TypeError, ValueError):
                raise APIResponseError(http_response.text)

        c = cls(http_response)
        c.response = http_response

        # TODO: Update rate-limits.  
        return c

    
    def __init__(self, http_response):
        self._raw = http_response
        self.json = http_response.json()

