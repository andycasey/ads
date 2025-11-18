"""Client for handling API requests to ADS."""

import asyncio
import aiohttp
import json
import os
import requests
import warnings
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from ads import logger, config
from .exceptions import APIResponseError
from .settings import ADSConfig, get_config

__version__ = "0.2.0"


class APIResponse:
    """A response from an ADS API end point."""

    response = None

    @classmethod
    def load_http_response(cls, http_response: requests.Response):
        if not http_response.ok:
            # Try to give an informed error message.
            for key in ("error", "message"):
                try:
                    raise APIResponseError(http_response.json()[key])
                except (KeyError, AttributeError, TypeError, ValueError):
                    continue
            else:
                raise APIResponseError(http_response.text)

        c = cls(http_response)
        c.response = http_response

        # Update rate limits
        RateLimits.set_from_http_response(http_response)

        return c

    @classmethod
    async def async_load_http_response(cls, http_response: aiohttp.ClientResponse):
        json_data = await http_response.json()
        if not http_response.ok:
            try:
                raise APIResponseError(json_data["error"])
            except (KeyError, AttributeError, TypeError, ValueError):
                text = await http_response.text()
                raise APIResponseError(text)

        c = cls(http_response, _json=json_data)
        c.response = http_response

        RateLimits.set_from_http_response(http_response)
        return c

    def __init__(self, http_response, _json=None):
        self._raw = http_response
        if _json is None:
            if hasattr(http_response, 'json'):
                if callable(http_response.json):
                    self.json = http_response.json()
                else:
                    self.json = http_response.json
            else:
                self.json = {}
        else:
            self.json = _json


class Client:
    """A class for handling API requests to ADS with token rotation and retry logic."""

    def __init__(self, config: Optional[ADSConfig] = None):
        """
        Initialize ADS API client.

        :param config: [optional]
            ADSConfig instance. If not provided, uses global config.
        """
        self.config = config or get_config()

        # Token rotation state
        self._current_token_index = 0

        # Session management - list of (session, token_index) tuples
        self._sessions: List[Tuple[aiohttp.ClientSession, int]] = []

        # Per-token rate limits - {token_index: {"remaining": N, "limit": M, "reset": T}}
        self._rate_limits: Dict[int, Dict[str, Optional[int]]] = {}

        # Synchronous session
        self._session: Optional[requests.Session] = None

        # Discover and set tokens if not already configured
        if self.config.tokens is None:
            discovered = self.config.discover_tokens()
            if discovered:
                self.config.tokens = discovered
            else:
                warnings.warn(
                    "No SAO/NASA ADS API token found. "
                    "See https://ads.readthedocs.io/en/v1/user/api-key.html for more details.",
                    RuntimeWarning
                )
                # Keep tokens as None - it will be handled properly when creating sessions

    @property
    def token(self) -> Optional[str]:
        """Return the current API token."""
        if self.config.tokens:
            return self.config.tokens[self._current_token_index]
        return None

    def _hit_rate_limit(self, token_index: int) -> bool:
        """Check if a specific token has hit its rate limit."""
        if token_index not in self._rate_limits:
            return False
        remaining = self._rate_limits[token_index].get("remaining", float('inf'))
        if remaining is None:
            return False
        return remaining <= self.config.rate_limit_threshold

    def _rotate_to_next_token(self) -> int:
        """Move to next token and return its index."""
        if self.config.tokens is None or len(self.config.tokens) <= 1:
            return self._current_token_index

        old_index = self._current_token_index
        self._current_token_index = (self._current_token_index + 1) % len(self.config.tokens)
        logger.info(f"Rotating from token {old_index} to token {self._current_token_index}")
        return self._current_token_index

    def _get_or_create_session(self) -> aiohttp.ClientSession:
        """Get current session or create new one if rate limit hit."""
        token_idx = self._current_token_index

        # Check if we need to rotate to next token
        if self._hit_rate_limit(token_idx):
            logger.info(f"Token {token_idx} hit rate limit, rotating...")
            token_idx = self._rotate_to_next_token()

        # Find existing session for this token
        for session, idx in self._sessions:
            if idx == token_idx and not session.closed:
                return session

        # Create new session for this token
        headers = {
            "User-Agent": f"ads-api-client/{__version__}",
            "Content-Type": "application/json"
        }

        # Add authorization header if token exists
        if self.config.tokens is not None and token_idx < len(self.config.tokens) and self.config.tokens[token_idx]:
            headers["Authorization"] = f"Bearer {self.config.tokens[token_idx]}"

        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit_per_host=self.config.async_limit_per_host,
                limit=self.config.async_limit,
            ),
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.config.async_timeout)
        )
        self._sessions.append((session, token_idx))
        return session

    def _update_rate_limits_from_response(self, token_idx: int, http_response):
        """Extract and store rate limit info for a specific token."""
        safe_int = lambda _: _ if _ is None else int(_)

        # Handle both requests.Response and aiohttp.ClientResponse
        if hasattr(http_response, 'headers'):
            headers = http_response.headers
        elif hasattr(http_response, 'response') and hasattr(http_response.response, 'headers'):
            headers = http_response.response.headers
        else:
            return

        self._rate_limits[token_idx] = {
            'limit': safe_int(headers.get('x-ratelimit-limit', None)),
            'remaining': safe_int(headers.get('x-ratelimit-remaining', None)),
            'reset': safe_int(headers.get('x-ratelimit-reset', None)),
        }

    async def get(self, end_point: str, params: Dict[str, Any], **kwargs) -> APIResponse:
        """
        Perform an async GET request with automatic retry and token rotation.

        :param end_point:
            The API end-point (e.g., '/search/query').

        :param params:
            Query parameters for the request.

        :param kwargs:
            Additional arguments to pass to the request.

        :returns:
            APIResponse object
        """
        uri = self.config.api_url + end_point
        session = self._get_or_create_session()
        token_idx = self._current_token_index

        for attempt in range(self.config.max_retries + 1):
            try:
                async with session.get(uri, params=params, **kwargs) as request:
                    # Check for error
                    if not request.ok:
                        if attempt < self.config.max_retries:
                            # Exponential backoff
                            wait_time = self.config.retry_base_delay * (2 ** attempt)
                            logger.warning(
                                f"Got {request.status} error, retrying in {wait_time}s "
                                f"(attempt {attempt + 1}/{self.config.max_retries})"
                            )
                            await asyncio.sleep(wait_time)
                            continue

                    response = await APIResponse.async_load_http_response(request)

                    # Update rate limits for this token
                    self._update_rate_limits_from_response(token_idx, response)
                    return response

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries:
                    wait_time = self.config.retry_base_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed: {e}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.config.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise

        # Should not reach here, but just in case
        raise APIResponseError("Max retries exceeded")

    async def post(self, end_point: str, params: Dict[str, Any] = None, **kwargs) -> APIResponse:
        """
        Perform an async POST request with automatic retry and token rotation.

        :param end_point:
            The API end-point.

        :param params:
            Query parameters.

        :param kwargs:
            Additional arguments (data, json, etc.)

        :returns:
            APIResponse object
        """
        uri = self.config.api_url + end_point
        session = self._get_or_create_session()
        token_idx = self._current_token_index

        for attempt in range(self.config.max_retries + 1):
            try:
                async with session.post(uri, params=params, **kwargs) as request:
                    if not request.ok:
                        if attempt < self.config.max_retries:
                            wait_time = self.config.retry_base_delay * (2 ** attempt)
                            logger.warning(
                                f"Got {request.status} error, retrying in {wait_time}s "
                                f"(attempt {attempt + 1}/{self.config.max_retries})"
                            )
                            await asyncio.sleep(wait_time)
                            continue

                    response = await APIResponse.async_load_http_response(request)
                    self._update_rate_limits_from_response(token_idx, response)
                    return response

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries:
                    wait_time = self.config.retry_base_delay * (2 ** attempt)
                    logger.warning(f"Request failed: {e}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise

        raise APIResponseError("Max retries exceeded")

    async def async_search(
        self,
        q: str,
        fl: List[str],
        rows: Optional[int] = None,
        sort: Optional[str] = None
    ):
        """
        Perform an asynchronous search query, fetching multiple pages if needed.
        Results are yielded as they complete (not in order) for maximum performance.

        :param q:
            The search query string.

        :param fl:
            List of fields to retrieve.

        :param rows: [optional]
            Maximum number of results to return. If None, returns all.

        :param sort: [optional]
            Sort order (default: 'entry_date desc').

        :yields:
            Document dictionaries as they are retrieved.
        """
        end_point = '/search/query'
        params = dict(
            q=q,
            fl=','.join(fl),
            sort=sort or 'entry_date desc',
            start=0,
            rows=min(
                self.config.max_rows_per_request,
                rows or self.config.max_rows_per_request
            )
        )

        # Get first page
        r = await self.get(end_point, params=params)
        for doc in r.json["response"]["docs"]:
            yield doc

        # Extract pagination info from first response
        num_found = r.json["response"]["numFound"]
        if rows is not None:
            num_found = min(num_found, rows)
        first_page_rows = len(r.json["response"]["docs"])
        remaining = num_found - first_page_rows

        if remaining <= 0:
            return

        # Calculate pages needed
        pages = remaining // self.config.max_rows_per_request
        if remaining % self.config.max_rows_per_request:
            pages += 1

        # Create coroutines for remaining pages
        coroutines = []
        for page in range(1, pages + 1):
            page_params = params.copy()
            page_params["start"] = page * self.config.max_rows_per_request
            coroutines.append(self.get(end_point, page_params))

        # Yield results as they complete
        for coroutine in asyncio.as_completed(coroutines):
            response = await coroutine
            for doc in response.json["response"]["docs"]:
                yield doc

    async def async_api_request(
        self,
        end_point: str,
        method: str = "get",
        start: int = 0,
        limit: Optional[int] = None,
        rows: int = 200,
        **kwargs
    ) -> List[APIResponse]:
        """
        Perform asynchronous API requests to fetch multiple pages of results concurrently.

        :param end_point:
            The API end-point.

        :param method:
            HTTP method (get or post).

        :param start:
            Starting index for results.

        :param limit:
            Maximum number of results to fetch. If None, fetches all.

        :param rows:
            Number of rows per request (max 200).

        :param kwargs:
            Additional request parameters.

        :returns:
            List of APIResponse objects.
        """
        if rows > 200:
            raise ValueError("rows cannot be greater than 200 (ADS maximum per request)")

        # Get the first page to determine total results
        method_lower = method.lower()
        if method_lower == "get":
            first_response = await self.get(end_point, kwargs.get('params', {}))
        elif method_lower == "post":
            first_response = await self.post(end_point, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        responses = [first_response]

        # Extract pagination info
        response_data = first_response.json
        num_found = response_data["response"]["numFound"]
        actual_rows = len(response_data["response"]["docs"])

        # Determine target total
        if limit is None:
            target_total = num_found
        else:
            target_total = min(limit, num_found)

        remaining_needed = target_total - actual_rows

        if remaining_needed <= 0:
            return responses

        # Calculate pages needed
        pages_needed = (remaining_needed + rows - 1) // rows

        logger.debug(f"Fetching {pages_needed} additional pages concurrently")

        # Create tasks for remaining pages
        tasks = []
        for page in range(1, pages_needed + 1):
            page_kwargs = kwargs.copy()
            page_params = page_kwargs.get('params', {}).copy()
            page_params['start'] = start + (page * rows)

            # For the last page, potentially reduce rows
            if limit is not None:
                remaining_for_this_page = target_total - actual_rows - ((page - 1) * rows)
                page_params['rows'] = min(rows, remaining_for_this_page)

            page_kwargs['params'] = page_params

            if method_lower == "get":
                task = self.get(end_point, page_params)
            else:
                task = self.post(end_point, **page_kwargs)

            tasks.append(task)

        # Execute all page requests concurrently
        try:
            additional_responses = await asyncio.gather(*tasks, return_exceptions=True)

            for response in additional_responses:
                if isinstance(response, Exception):
                    logger.error(f"Error fetching page: {response}")
                else:
                    responses.append(response)

        except Exception as e:
            logger.error(f"Error in concurrent page fetching: {e}")

        return responses

    # Async context manager support
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_all_sessions()
        return None

    async def close_all_sessions(self):
        """Close all active aiohttp sessions."""
        for session, _ in self._sessions:
            if not session.closed:
                await session.close()
        self._sessions = []

    # Synchronous API (for backward compatibility)
    @property
    def session(self) -> requests.Session:
        """A client session for performing synchronous HTTP requests."""
        if self._session is None:
            self._session = requests.Session()
            headers = {
                "User-Agent": f"ads-api-client/{__version__}",
                "Content-Type": "application/json"
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._session.headers.update(headers)
        return self._session

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self.__del__()

    def __del__(self):
        try:
            if self._session:
                self._session.close()
        finally:
            return None

    def _api_url(self, end_point: str) -> str:
        """Construct full API URL from endpoint."""
        return "/".join(map(lambda _: _.strip("/"), [self.config.api_url, end_point]))

    def api_request(self, end_point: str, method: str = "get", **kwargs) -> APIResponse:
        """
        Perform a synchronous API request (for backward compatibility).

        :param end_point:
            The API end-point (e.g., '/search/query').

        :param method:
            The HTTP method to use (default: get).

        :param kwargs:
            Additional request arguments.

        :returns:
            APIResponse object
        """
        method = method.lower().strip()
        if method not in ("get", "post", "put", "delete"):
            raise ValueError(f"Invalid method: {method}")

        url = self._api_url(end_point)
        response = getattr(self.session, method)(url, **kwargs)
        return APIResponse.load_http_response(response)


class _Singleton(type):
    """A metaclass for singletons."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RateLimits(object, metaclass=_Singleton):
    """A singleton to store ADS service rate limits."""

    services = {
        "search": "solr",
        "biblib": "biblib",
        "export": "export",
        "metrics": "metrics",
    }
    limits = {}

    @classmethod
    def get_rate_limits(cls, service: str) -> dict:
        return cls().limits.get(service, {})

    @classmethod
    def get_service(cls, url: str) -> str:
        """
        Return the ADS service given a URL.

        :param url:
            The requested URL.
        """
        api_url = get_config().api_url
        end_point = str(url)[len(api_url):].lstrip("/")
        collection = end_point.split("/")[0]
        return cls.services.get(collection, collection)

    @classmethod
    def set_from_http_response(cls, http_response) -> None:
        """
        Set the current rate limits from the given HTTP response.

        :param http_response:
            The HTTP response (requests.Response or aiohttp.ClientResponse).
        """
        safe_int = lambda _: _ if _ is None else int(_)

        # Get URL - handle both requests and aiohttp responses
        if hasattr(http_response, 'url'):
            url = str(http_response.url)
        elif hasattr(http_response, 'response') and hasattr(http_response.response, 'url'):
            url = str(http_response.response.url)
        else:
            return

        # Get headers
        if hasattr(http_response, 'headers'):
            headers = http_response.headers
        elif hasattr(http_response, 'response') and hasattr(http_response.response, 'headers'):
            headers = http_response.response.headers
        else:
            return

        service = cls.get_service(url)
        cls().set(
            service,
            **{
                'limit': safe_int(headers.get('x-ratelimit-limit', None)),
                'remaining': safe_int(headers.get('x-ratelimit-remaining', None)),
                'reset': safe_int(headers.get('x-ratelimit-reset', None)),
            }
        )

    def set(self, service: str, **kwargs) -> None:
        """
        Set the limits for an ADS service.

        :param service:
            The service name (e.g., solr).

        :param kwargs:
            The keyword arguments to set for the limits.
        """
        self.limits.setdefault(service, {}).update(kwargs)

    def to_dict(self) -> dict:
        return self.limits

    def __str__(self) -> str:
        return json.dumps(self.limits, indent=2, default=str)


class SearchQuery:
    def __init__(self, **kwargs):
        raise NotImplementedError("Despite what the docs say, this backward-compatibility is not done yet")
