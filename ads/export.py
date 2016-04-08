"""
interfaces to the adsws export service
"""

import json
import six
import os

from .base import APIResponse, BaseQuery
from .config import EXPORT_URL
from .tests.mocks import MockExportResponse


class ExportResponse(APIResponse):
    """
    Data structure that represents a response from the ads metrics service
    """
    def __init__(self, raw):
        self._raw = raw
        self.result = json.loads(raw)['export']

    def __str__(self):
        if six.PY3:
            return self.__unicode__()
        return self.__unicode__().encode("utf-8")

    def __unicode__(self):
        return self.result


class ExportQuery(BaseQuery):
    """
    Represents a query to the adsws metrics service
    """

    HTTP_ENDPOINT = EXPORT_URL
    FORMATS = ['bibtex', 'endnote', 'aastex']
    _response = None
    MockResponse = MockExportResponse
    _name = '/export'

    def __init__(self, bibcodes, format="bibtex", test=False):
        """
        :param bibcodes: Bibcodes to send to in the metrics query
        :type bibcodes: list or string
        :param format: format to
        """
        super(ExportQuery, self).__init__(test=test)

        assert format in self.FORMATS, "Format must be one of {}".format(
            self.FORMATS)

        self.format = format

        self.response = None  # current ExportResponse object
        if isinstance(bibcodes, six.string_types):
            bibcodes = [bibcodes]
        self.bibcodes = bibcodes
        self.json_payload = json.dumps({"bibcode": bibcodes})

    def _execute(self):
        """
        Execute the http request to the metrics service
        :return ads-classic formatted export string
        """
        url = os.path.join(self.HTTP_ENDPOINT, self.format)
        self.response = ExportResponse.load_http_response(
            self.session.post(url, data=self.json_payload)
        )
        ExportQuery._response = self.response
        return self.response.result