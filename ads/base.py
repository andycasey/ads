import collections
import aiohttp
import asyncio
import os
import json
import requests
import warnings

from ads import logger, config
from .exceptions import APIResponseError

__version__ = "0.2.0"


class BaseQuery(object):

    _token = config.token
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
            for v in map(os.environ.get, config.TOKEN_ENVIRON_VARS):
                if v is not None:
                    self._token = v
                    return self._token
            for f in config.TOKEN_FILES:
                try:
                    with open(f) as fp:
                        self._token = fp.read().strip()
                        return self._token
                except IOError:
                    pass
            if config.token is not None:
                self._token = config.token
                return self._token
            warnings.warn(
                "No SAO/NASA ADS API token found. "
                "See https://ads.readthedocs.io/en/v1/user/api-key.html for more details.", 
                RuntimeWarning
            )
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
                # We are going to be good citizens and limit the number of simultaneous connections.
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
        return self.__del__()

    def __del__(self):
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
            raise ValueError(
                f"Method '{method}' not available. "
                f"Available methods: {', '.join(available_methods)}"
            )
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

    # May need to get explicit information from ADS team on how end points
    # and service limits relate.
    services = {
        "search": "solr",
        "biblib": "biblib",
        "export": "export",
        "metrics": "metrics",
    }
    limits = {}
        
    @classmethod
    def get_rate_limits(cls, service):
        return cls().limits[service]
        
    @classmethod
    def get_service(cls, url):
        """
        Return the ADS service given a URL.

        :param url:
            The requested URL.
        """
        end_point = url[len(config.ADSWS_API_URL):].lstrip("/")
        collection = end_point.split("/")[0]
        try:
            return cls.services[collection]
        except:
            raise KeyError(f"Cannot infer service from end point {end_point} ({url})")

    @classmethod
    def set_from_http_response(cls, http_response):
        """
        Set the current rate limits from the given HTTP response.
        
        :param service:
            The ADS service name.

        :param http_response:
            The HTTP response.
        """
        service = cls.get_service(http_response.url)
        cls().set(
            service, 
            **{
                'limit': http_response.headers.get('x-ratelimit-limit', None),
                'remaining': http_response.headers.get('x-ratelimit-remaining', None),
                'reset': http_response.headers.get('x-ratelimit-reset', None),
            }
        )
        # TODO: Does this apply to ExportQuery and MetricsQuery?
        #if "max_rows" not in self.limits and has_multiple_pages(response):
        #    self.limits["max_rows"] = response.json()["responseHeader"]["para"]
        
    def set(self, service, **kwargs):
        """
        Set the limits for an ADS service.
        
        :param service:
            The service name (e.g., solr).
        
        :param kwargs:
            The keyword arguments to set for the limits (e.g., limit, remaining, reset).
        """
        self.limits.setdefault(service, {}).update(kwargs)

    def to_dict(self):
        return self.limits

    def __str__(self):
        return json.dumps(self.limits)


def has_multiple_pages(response):
    data = response.json()
    num_found = data["response"]["numFound"]
    start = data["response"]["start"]
    rows = data["responseHeader"]["params"]["rows"]
    if (num_found - start) > rows:
        return True
    return False


class APIResponse(object):

    """ A response from an ADS API end point. """

    response = None

    @classmethod
    def load_http_response(cls, http_response):
        if not http_response.ok:
            # Try to give an informed error message.
            try:
                raise APIResponseError(http_response.json()["error"])
            except (KeyError, AttributeError, TypeError, ValueError):
                raise APIResponseError(http_response.text)

        c = cls(http_response)
        c.response = http_response

        # We used to get rate limits from the class name, and have inherited classes
        # for all different service requests and response. 
        # But that meant response objects that had inconsistent attributes, and some
        # services only have one end point.
        RateLimits.set_from_http_response(http_response)

        return c

    def __init__(self, http_response):
        self._raw = http_response
        self.json = http_response.json()