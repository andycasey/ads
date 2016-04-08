"""
interfaces to the adsws metrics service
"""

import json
import six

from .base import APIResponse, BaseQuery
from .config import METRICS_URL
from .tests.mocks import MockMetricsResponse


class MetricsResponse(APIResponse):
    """
    Data structure that represents a response from the ads metrics service
    """
    def __init__(self, raw):
        self._raw = raw
        self.metrics = json.loads(raw)

    def __str__(self):
        if six.PY3:
            return self.__unicode__()
        return self.__unicode__().encode("utf-8")

    def __unicode__(self):
        return self.metrics


class MetricsQuery(BaseQuery):
    """
    Represents a query to the adsws metrics service
    """

    HTTP_ENDPOINT = METRICS_URL
    MockResponse = MockMetricsResponse
    _response = None
    _name = '/metrics'

    def __init__(self, bibcodes, test=False):
        """
        :param bibcodes: Bibcodes to send to in the metrics query
        :type bibcodes: list or string
        """
        super(MetricsQuery, self).__init__(test=test)

        self.response = None  # current MetricsResponse object
        if isinstance(bibcodes, six.string_types):
            bibcodes = [bibcodes]
        self.bibcodes = bibcodes
        self.json_payload = json.dumps({"bibcodes": bibcodes})

    def _execute(self):
        """
        Execute the http request to the metrics service
        """
        self.response = MetricsResponse.load_http_response(
            self.session.post(self.HTTP_ENDPOINT, data=self.json_payload)
        )
        MetricsQuery._response = self.response
        return self.response.metrics