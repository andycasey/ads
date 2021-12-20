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


class Client:
    
    _token = config.token
    _async_limit_per_host = 10
        
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
                    connector=aiohttp.TCPConnector(limit_per_host=self._async_limit_per_host),
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

    def _api_method_cleaned(self, method):
        available_methods = ("get", "post", "put", "delete")
        cleaned_method = method.lower().strip()
        if cleaned_method not in available_methods:
            raise ValueError(
                f"Method '{method}' not available. "
                f"Available methods: {', '.join(available_methods)}"
            )
        return cleaned_method

    def _api_request(self, end_point, method, **kwargs):
        """
        Perform a synchronous API request.
        
        :param end_point:
            The API end-point (e.g., '/search/query').
                
        :param method:
            The HTTP method to use for the request (default: GET).

        :param kwargs: [optional]
            Keyword arguments to pass to the `requests.request` method.
            Examples include `data`, `params`, etc.

        :returns:
            An `APIResponse` object.
        """
        method = self._api_method_cleaned(method)
        return APIResponse.load_http_response(
            getattr(self.session, method)(self._api_url(end_point), **kwargs)
        )

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
        return self._api_request(end_point, method, **kwargs)

    def _api_url(self, end_point):
        return "/".join(map(lambda _: _.strip("/"), [config.ADSWS_API_URL, end_point]))


    # Asynchronous context manager.
    """
    def __aenter__(self):
        print("in __aenter__")
        return self

    def __await__(self):
        return self.__anext__()

    def __aexit__(self, exc_type, exc, tb):
        print(f"in __aexit__")
        try:
            self.async_session.close()
        finally:
            return None
    """

    async def _async_api_request(self, async_session, end_point, params, method, **kwargs):
        
        url = self._api_url(end_point)
        method = self._api_method_cleaned(method)
        callable = getattr(async_session, method)
        try:
            logger.debug(f"Querying {url} with {params} with {method}")
            async with callable(url, params=params) as request:
                logger.debug(f"\tawaiting response on {params}")
                logger.debug(f"Retrieved response from {url} with {params}")
                return await APIResponse.async_load_http_response(request)

        except asyncio.CancelledError:
            logger.debug(f"Cancelled request to {url} with {params}")
            raise

    async def async_api_request(self, async_session, end_point, params, method="GET", **kwargs):
        return self._async_api_request(async_session, end_point, params, method, **kwargs)


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
        end_point = str(url)[len(config.ADSWS_API_URL):].lstrip("/")
        collection = end_point.split("/")[0]
        # TODO: Raise a warning if we can't identify the service?        
        return cls.services.get(collection, collection)

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


class APIResponse:

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

    @classmethod
    async def async_load_http_response(cls, http_response):
        json = await http_response.json()
        if not http_response.ok:
            try:
                raise APIResponseError(json["error"])
            except (KeyError, AttributeError, TypeError, ValueError):
                raise APIResponseError(await http_response.text)

        c = cls(http_response, _json=json)
        c.response = http_response
        
        RateLimits.set_from_http_response(http_response)
        return c
        

    def __init__(self, http_response, _json=None):
        self._raw = http_response
        if _json is None:
            self.json = http_response.json()
        else:
            self.json = _json