"""
Mock responses
"""

from httpretty import HTTPretty
from stubdata.solr import example_solr_response
import json
from collections import OrderedDict


class HTTPrettyMock(object):
    """
    httpretty context manager scaffolding
    """

    def __enter__(self):
        HTTPretty.enable()

    def __exit__(self, etype, value, traceback):
        """
        :param etype: exit type
        :param value: exit value
        :param traceback: the traceback for the exit
        """
        HTTPretty.reset()
        HTTPretty.disable()


class MockSolrResponse(HTTPrettyMock):
    """
    context manager that mocks a Solr response
    """
    def __init__(self, api_endpoint):
        """
        :param api_endpoint: name of the API end point
        """

        self.api_endpoint = api_endpoint

        def request_callback(request, uri, headers):
            """
            :param request: HTTP request
            :param uri: URI/URL to send the request
            :param headers: header of the HTTP request
            :return: httpretty response
            """

            resp = json.loads(example_solr_response)
            rows = int(
                request.querystring.get(
                    'rows', [len(resp['response']['docs'])]
                )[0]
            )
            start = int(request.querystring.get('start', [0])[0])
            try:
                resp['response']['docs'] = resp['response']['docs'][start:start+rows]
            except IndexError:
                resp['response']['docs'] = resp['response']['docs'][start:]

            return 200, headers, json.dumps(resp)

        HTTPretty.register_uri(
            HTTPretty.GET,
            self.api_endpoint,
            body=request_callback,
            content_type="application/json"
        )