import aiohttp
import os
import requests
import warnings

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

    
    
class APIResponse(object):

    response = None


    @classmethod
    def load_http_response(cls, http_response):

        


        if not http_response.ok:
            raise RuntimeError(http_response.text) # Toodo