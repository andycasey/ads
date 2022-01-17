"""
Sandbox environment that wraps relevant classes so that they receive mock
responses rather than contact the live API
"""

import re
from .tests.mocks import MockApiResponse, MockSolrResponse, MockMetricsResponse, \
    MockExportResponse


from ads.library import Library as _Library


class Library(_Library):
    """
    A library that uses mock responses instead of contacting the live API
    """

    def api_request(self, end_point, method="GET", **kwargs):

        url = self._api_url(end_point)

        method_func = self._api_request_callable(method)
        return APIResponse.load_http_response(method_func(url, **kwargs))